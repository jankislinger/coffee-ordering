CLI := 'uv run --env-file .env -m coffee_ordering.cli'

roaster := 'dosmundos'
date := '2026-04-03'

run:
    @just list-products
    auggie --print --instruction-file instruction.txt
    @just add-to-cart

run-aggregates:
    uv run scripts/aggregates.py --date {{date}} --roaster {{roaster}}

list-products:
    {{CLI}} list-products --roaster {{roaster}} > orders/{{date}}/products.txt

add-to-cart:
    {{CLI}} add-to-cart --roaster {{roaster}} --list orders/{{date}}/shopping_list.txt

