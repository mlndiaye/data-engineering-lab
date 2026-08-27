select *
from {{ ref('pr_metrics') }}
where merge_duration_hours < 0
