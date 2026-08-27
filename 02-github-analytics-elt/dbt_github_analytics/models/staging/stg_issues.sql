select
    id                  as issue_id,
    number              as issue_number,
    title               as issue_title,
    state               as issue_state,
    created_at          as issue_created_at,
    closed_at           as issue_closed_at,
    updated_at          as issue_updated_at,
    json_value(user, '$.login')  as author_login,
    repository

from {{ source('github', 'issues') }}
where pull_request is null
