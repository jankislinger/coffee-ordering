RUN_UV := 'uv run --env-file .env'
CLI := 'uv run --env-file .env -m coffee_ordering.cli'

roaster := 'doubleshot'
# roaster := 'dosmundos'
date := '2026-06-05'

run:
    @just list-products
    auggie --print --instruction-file instruction.txt
    @just run-aggregates
    @just add-to-cart

run-aggregates:
    {{RUN_UV}} scripts/aggregates.py --date {{date}} --roaster {{roaster}}

list-products:
    {{CLI}} list-products --roaster {{roaster}} > orders/{{date}}/products.txt

add-to-cart:
    {{CLI}} add-to-cart --roaster {{roaster}} --list orders/{{date}}/shopping_list.txt

