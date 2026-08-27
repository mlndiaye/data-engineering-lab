{% macro merge_speed(merged_at_column, created_at_column) %}
    case
        when {{ merged_at_column }} is null then 'Not merged'
        when timestamp_diff({{ merged_at_column }}, {{ created_at_column }}, hour) <= 24 then 'Fast'
        when timestamp_diff({{ merged_at_column }}, {{ created_at_column }}, hour) <= 72 then 'Medium'
        else 'Slow'
    end
{% endmacro %}
