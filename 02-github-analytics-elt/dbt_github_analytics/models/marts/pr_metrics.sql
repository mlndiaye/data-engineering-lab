select
    pr_id,
    pr_number,
    pr_title,
    author_login,
    pr_state,
    pr_created_at,
    pr_merged_at,
    timestamp_diff(pr_merged_at, pr_created_at, hour) as merge_duration_hours,
    {{ merge_speed('pr_merged_at', 'pr_created_at') }} as merge_speed

from {{ ref('stg_pull_requests') }}
