with first_review as (
    select
        pr_number,
        min(review_submitted_at) as first_review_at
    from {{ ref('stg_reviews') }}
    group by pr_number
)

select
    pr.pr_id,
    pr.pr_number,
    pr.pr_title,
    pr.author_login,
    pr.pr_created_at,
    fr.first_review_at,
    timestamp_diff(fr.first_review_at, pr.pr_created_at, hour) as time_to_first_review_hours

from {{ ref('stg_pull_requests') }} pr
left join first_review fr
    on pr.pr_number = fr.pr_number
