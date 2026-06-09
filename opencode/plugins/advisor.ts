import { type Plugin, tool } from "@opencode-ai/plugin"
import type { ToolContext } from "@opencode-ai/plugin/dist/tool.js"

// Token estimation: ~4 chars per token
const CHARS_PER_TOKEN = 4
const MAX_CONTEXT_TOKENS = 100_000
const MAX_CONTEXT_CHARS = MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN
const MAX_ADVISOR_CALLS = 3

// Patterns to sanitize before sending to advisor
const SECRET_PATTERNS = [
  /(?:api[_-]?key|apikey|secret|token|password|passwd|credential|auth)[\s]*[=:]\s*["']?[A-Za-z0-9_\-/.+=]{16,}["']?/gi,
  /(?:sk|pk|rk|ak)-[A-Za-z0-9]{20,}/g,
  /ghp_[A-Za-z0-9]{36,}/g,
  /eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g,
]

function sanitizeSecrets(text: string): string {
  let result = text
  for (const pattern of SECRET_PATTERNS) {
    result = result.replace(pattern, "[REDACTED]")
  }
  return result
}

interface FlatMessage {
  role: string
  text: string
}

function truncateTranscript(messages: FlatMessage[]): string {
  const full = messages.map((m) => `[${m.role}]: ${m.text}`).join("\n\n")

  if (full.length <= MAX_CONTEXT_CHARS) {
    return sanitizeSecrets(full)
  }

  const firstMessages = messages.slice(0, 5)
  const firstPart = firstMessages
    .map((m) => `[${m.role}]: ${m.text}`)
    .join("\n\n")

  const remainingBudget = MAX_CONTEXT_CHARS - firstPart.length - 200
  if (remainingBudget <= 0) {
    return sanitizeSecrets(firstPart)
  }

  const lastPart = full.slice(-remainingBudget)
  const truncatedTokens = Math.round(remainingBudget / CHARS_PER_TOKEN)
  const result = `${firstPart}\n\n[... transcript truncated — showing last ~${truncatedTokens} tokens ...]\n\n${lastPart}`

  return sanitizeSecrets(result)
}

// In-memory call counter per session
const callCounts = new Map<string, number>()

/**
 * Consult the senior strategic advisor.
 *
 * This tool reads the full session transcript, sends it to a larger model
 * (the "advisor" agent), and returns strategic guidance.
 *
 * The advisor has NO tools — it only thinks and returns a short plan.
 */
export const AdvisorPlugin: Plugin = async ({ client }) => {
  return {
    tool: {
      advisor_consult: tool({
        description:
          "Consult a senior strategic advisor for guidance on complex decisions. " +
          "Use BEFORE starting substantial work, when stuck after 2+ attempts, " +
          "before declaring done on complex tasks, or before changing approach. " +
          "The advisor sees your full conversation history and provides strategic direction in under 100 words.",
        args: {
          question: tool.schema
            .string()
            .describe(
              "What you need guidance on. Be specific: include what you have tried, " +
              "what failed, and what you are considering.",
            ),
        },
        async execute(args, context: ToolContext) {
          const sessionID = context.sessionID

          // Enforce max calls per session
          const currentCount = callCounts.get(sessionID) ?? 0
          if (currentCount >= MAX_ADVISOR_CALLS) {
            return (
              `Advisor limit reached (${MAX_ADVISOR_CALLS} calls per session). ` +
              "Continue with your best judgment. If still stuck, ask the user for guidance."
            )
          }
          callCounts.set(sessionID, currentCount + 1)

          try {
            // 1. Read full transcript via SDK client
            const messagesRes = await client.session.messages({
              path: { id: sessionID },
            })

            if (!messagesRes.data) {
              return "Advisor unavailable: could not read session messages. Continue with your best judgment."
            }

            // 2. Flatten messages into readable transcript
            const flatMessages: FlatMessage[] = []
            const messageList = Array.isArray(messagesRes.data) ? messagesRes.data : []
            for (const msg of messageList) {
              const role = msg?.info?.role ?? "unknown"
              const textParts: string[] = []
              const parts = Array.isArray(msg?.parts) ? msg.parts : []
              for (const part of parts) {
                if (part?.type === "text" && typeof part?.text === "string") {
                  textParts.push(part.text)
                } else if (part?.type === "tool-invocation") {
                  const toolName = part?.toolName ?? "unknown-tool"
                  const input = part?.input ? JSON.stringify(part.input).slice(0, 500) : ""
                  const output = part?.state === "completed" && part?.output
                    ? JSON.stringify(part.output).slice(0, 500)
                    : ""
                  textParts.push(
                    `[Tool: ${toolName}] Input: ${input}${output ? ` Output: ${output}` : ""}`,
                  )
                }
              }
              if (textParts.length > 0) {
                flatMessages.push({ role: String(role), text: textParts.join("\n") })
              }
            }

            // 3. Build truncated transcript
            const transcript = truncateTranscript(flatMessages)

            // 4. Create temporary advisor session via SDK client
            const createRes = await client.session.create({
              body: { title: `advisor-${Date.now()}` },
            })

            if (!createRes.data?.id) {
              return "Advisor unavailable: session creation failed. Continue with your best judgment."
            }

            const advisorSessionId = createRes.data.id

            // 5. Send transcript + question to the advisor session via SDK client
            const promptRes = await client.session.prompt({
              path: { id: advisorSessionId },
              body: {
                parts: [
                  {
                    type: "text",
                    text: [
                      "## Full Session Transcript",
                      "",
                      transcript,
                      "",
                      "## Question",
                      "",
                      args.question,
                      "",
                      "Respond with a clear, actionable plan in under 100 words using enumerated steps.",
                    ].join("\n"),
                  },
                ],
                // Use the advisor agent which is configured with a larger model
                agent: "advisor",
              },
            })

            if (!promptRes.data) {
              return "Advisor unavailable: prompt failed. Continue with your best judgment."
            }

            // 6. Extract the assistant text from the prompt response
            let advisorResponse = ""
            const parts = Array.isArray(promptRes.data.parts) ? promptRes.data.parts : []
            for (const part of parts) {
              if (part?.type === "text" && typeof part?.text === "string") {
                advisorResponse += part.text
              }
            }

            if (!advisorResponse) {
              return "Advisor returned empty response. Continue with your best judgment."
            }

            const callNum = callCounts.get(sessionID) ?? 1
            return `[Advisor guidance — call ${callNum}/${MAX_ADVISOR_CALLS}]\n\n${advisorResponse}`
          } catch (error) {
            const message = error instanceof Error ? error.message : String(error)
            return `Advisor unavailable: ${message}. Continue with your best judgment.`
          }
        },
      }),
    },
  }
}
