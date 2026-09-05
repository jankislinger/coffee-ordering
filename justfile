RUN_UV := 'uv run --env-file .env'
CLI := 'uv run --env-file .env -m coffee_ordering.cli'

roaster := 'doubleshot'
#roaster := 'dosmundos'
date := '2026-08-28'

slack_url := 'https://sky.slack.com/archives/C08A72XKNJY/p1787903630552429'

_default:
    @just --list

run:
    @just list-products
    @just create-orders
    @just run-aggregates
    @just add-to-cart

run-aggregates:
    {{RUN_UV}} scripts/aggregates.py --date {{date}} --roaster {{roaster}}

list-products:
    mkdir -p orders/{{date}}
    {{CLI}} list-products --roaster {{roaster}} > orders/{{date}}/products.txt

add-to-cart:
    {{CLI}} add-to-cart --roaster {{roaster}} --list orders/{{date}}/shopping_list.txt

# Create structured list of items to order
create-orders:
    #!/usr/bin/env -S auggie --print
    Create structured list of items to order.

    Source file:
    - thread at {{slack_url}}
    - list of products from the selected roaster: orders/{{date}}/products.txt

    Output:
    - json file at orders/{{date}}/orders.json
    - keys: person (str), product_id (str), variant_id (str), quantity (int)
