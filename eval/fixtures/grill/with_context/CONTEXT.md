# Domain Glossary

## Language
**Cliente**: A person or organization that places orders. _Avoid_: customer, buyer, user
**Pedido**: A request for products from a Cliente. _Avoid_: order, purchase, transaction
**Producto**: An item available for sale. _Avoid_: item, good, SKU

## Relationships
- A **Cliente** places zero or more **Pedidos**
- A **Pedido** contains one or more **Productos**

## Flagged ambiguities
- "account" → resolved: refers to Cliente login, NOT billing account
