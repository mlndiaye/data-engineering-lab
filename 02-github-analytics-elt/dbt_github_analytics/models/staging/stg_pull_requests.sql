select
    id                  as pr_id,
    number              as pr_number,
    title               as pr_title,
    state               as pr_state,
    draft               as is_draft,
    created_at          as pr_created_at,
    merged_at           as pr_merged_at,
    closed_at           as pr_closed_at,
    updated_at          as pr_updated_at,
    json_value(user, '$.login')  as author_login,
    repository

from {{ source('github', 'pull_requests') }}
