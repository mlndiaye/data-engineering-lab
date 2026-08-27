select
    id                          as review_id,
    state                       as review_state,
    json_value(user, '$.login') as reviewer_login,
    submitted_at                as review_submitted_at,
    cast(regexp_extract(pull_request_url, r'/pulls/(\d+)$') as int64) as pr_number,
    repository

from {{ source('github', 'reviews') }}
