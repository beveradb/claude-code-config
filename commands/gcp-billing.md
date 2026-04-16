---
description: Analyze GCP billing - daily trends, service breakdown, IaC mapping, cost optimization
allowed-tools: Bash, Read, Glob, Grep, Task, AskUserQuestion, WebSearch
---

# GCP Billing Analysis

Analyze GCP billing data to understand cloud spend, map costs to infrastructure code, and identify optimization opportunities.

**Usage:** `/gcp-billing [--days N] [--project PROJECT_ID]`

Arguments: $ARGUMENTS

## Configuration

```
DEFAULT_DAYS=30
BILLING_EXPORT_DATASET=billing_export
```

## Workflow Overview

```
Step 1: Detect GCP Project & Billing Configuration
       ↓
Step 2: Query Billing Data (BigQuery or Billing API)
       ↓
Step 3: Daily Spend Trends
       ↓
Step 4: Service Breakdown
       ↓
Step 5: Map to IaC Resources
       ↓
Step 6: Cost Attribution Analysis
       ↓
Step 7: Identify Optimization Opportunities
       ↓
Step 8: Present Recommendations
```

## Instructions

### Step 1: Detect GCP Project & Billing Configuration

First, identify the GCP project from $ARGUMENTS or detect from current repo:

```bash
echo "=== GCP BILLING ANALYSIS ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Try to detect project from Pulumi config or gcloud
PROJECT_ID="${PROJECT_ID:-}"

# Check for Pulumi config
if [ -z "$PROJECT_ID" ]; then
  # Look for Pulumi.prod.yaml or Pulumi.yaml
  for config_file in Pulumi.prod.yaml Pulumi.yaml infrastructure/Pulumi.prod.yaml infrastructure/Pulumi.yaml; do
    if [ -f "$config_file" ]; then
      PROJECT_ID=$(grep -E "gcp:project:|project:" "$config_file" | head -1 | sed 's/.*: *//' | tr -d '"' | tr -d "'")
      [ -n "$PROJECT_ID" ] && break
    fi
  done
fi

# Fall back to gcloud default
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
fi

echo "Project: $PROJECT_ID"

# Get billing account
BILLING_ACCOUNT=$(gcloud billing projects describe "$PROJECT_ID" --format="value(billingAccountName)" 2>/dev/null | sed 's/billingAccounts\///')
echo "Billing Account: $BILLING_ACCOUNT"
```

### Step 2: Check BigQuery Billing Export

Check if billing data is exported to BigQuery (required for detailed analysis):

```bash
echo ""
echo "STEP 2: Checking BigQuery Billing Export"
echo "========================================="

# List datasets looking for billing export
BILLING_DATASET=$(bq ls --project_id="$PROJECT_ID" 2>/dev/null | grep -E "billing|cost" | awk '{print $1}' | head -1)

if [ -n "$BILLING_DATASET" ]; then
  echo "Found billing dataset: $BILLING_DATASET"

  # Check for the standard billing export table
  BILLING_TABLE=$(bq ls --project_id="$PROJECT_ID" "$BILLING_DATASET" 2>/dev/null | grep -E "gcp_billing_export|cloud_pricing_export" | awk '{print $1}' | head -1)

  if [ -n "$BILLING_TABLE" ]; then
    echo "Found billing export table: $BILLING_DATASET.$BILLING_TABLE"
    echo "BigQuery billing export is configured - can run detailed analysis"
  else
    echo "Dataset exists but no standard billing export table found"
    echo "Tables in dataset:"
    bq ls --project_id="$PROJECT_ID" "$BILLING_DATASET" 2>/dev/null
  fi
else
  echo "No BigQuery billing export dataset found"
  echo ""
  echo "To enable detailed billing analysis, set up BigQuery billing export:"
  echo "1. Go to: https://console.cloud.google.com/billing"
  echo "2. Select your billing account"
  echo "3. Click 'Billing export' in the left menu"
  echo "4. Enable 'Standard usage cost' export to BigQuery"
  echo ""
  echo "Falling back to Cloud Billing API (limited data)..."
fi
```

If BigQuery export is not configured, proceed with Cloud Billing API (limited but still useful).

### Step 3: Query Billing Data

#### Option A: BigQuery (Detailed)

If BigQuery billing export is available:

```bash
DAYS=${1:-30}
echo ""
echo "STEP 3: Querying Billing Data (Last $DAYS days)"
echo "================================================"

# Daily cost summary
bq query --use_legacy_sql=false --project_id="$PROJECT_ID" --format=prettyjson "
SELECT
  DATE(usage_start_time) as date,
  ROUND(SUM(cost), 2) as daily_cost,
  currency
FROM \`$PROJECT_ID.$BILLING_DATASET.$BILLING_TABLE\`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL $DAYS DAY)
GROUP BY date, currency
ORDER BY date DESC
LIMIT 60
"
```

#### Option B: Billing API (Basic)

If BigQuery is not available, use billing budgets as a proxy:

```bash
echo ""
echo "STEP 3: Checking Billing Budgets & Recent Invoices"
echo "==================================================="

# List budgets (shows spend thresholds and current amounts)
gcloud billing budgets list --billing-account="$BILLING_ACCOUNT" --format=json 2>/dev/null

# This gives us budget amounts and current spend vs budget
```

### Step 4: Service Breakdown

Analyze costs by GCP service (SKU):

```bash
echo ""
echo "STEP 4: Cost Breakdown by Service"
echo "=================================="

# If BigQuery available:
bq query --use_legacy_sql=false --project_id="$PROJECT_ID" --format=prettyjson "
SELECT
  service.description as service,
  ROUND(SUM(cost), 2) as total_cost,
  currency,
  COUNT(DISTINCT sku.description) as sku_count
FROM \`$PROJECT_ID.$BILLING_DATASET.$BILLING_TABLE\`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL $DAYS DAY)
GROUP BY service.description, currency
ORDER BY total_cost DESC
LIMIT 20
"
```

Also get SKU-level breakdown for top services:

```bash
# Top SKUs by cost
bq query --use_legacy_sql=false --project_id="$PROJECT_ID" --format=prettyjson "
SELECT
  service.description as service,
  sku.description as sku,
  ROUND(SUM(cost), 2) as total_cost,
  ROUND(SUM(usage.amount), 2) as usage_amount,
  usage.unit as usage_unit,
  currency
FROM \`$PROJECT_ID.$BILLING_DATASET.$BILLING_TABLE\`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL $DAYS DAY)
GROUP BY service.description, sku.description, usage.unit, currency
ORDER BY total_cost DESC
LIMIT 30
"
```

### Step 5: Map to IaC Resources

Search the current repo for infrastructure code to map costs to specific resources.

**Look for these IaC patterns:**

1. **Pulumi (Python/TypeScript)**
   - `infrastructure/` directory
   - `Pulumi.yaml`, `Pulumi.*.yaml`
   - Resource definitions in `__main__.py` or modules

2. **Terraform**
   - `*.tf` files
   - `terraform/` directory
   - Resource blocks

3. **Cloud Run Services** (common in Aquarius)
   - Map `Cloud Run` costs to services in `modules/cloud_run.py`
   - Check service configs for CPU/memory allocations

4. **Firestore**
   - Document reads/writes → usage patterns in code
   - Index definitions → `modules/firestore.py`

5. **Secrets Manager**
   - Number of secrets → `modules/secrets.py`

```bash
echo ""
echo "STEP 5: Finding IaC Resources"
echo "=============================="

# Find infrastructure directories
echo "Infrastructure locations found:"
find . -type d -name "infrastructure" -o -type d -name "terraform" -o -type d -name "pulumi" 2>/dev/null | head -10

# Find Pulumi files
echo ""
echo "Pulumi configs:"
find . -name "Pulumi*.yaml" 2>/dev/null | head -10

# Find Terraform files
echo ""
echo "Terraform files:"
find . -name "*.tf" 2>/dev/null | head -10
```

Read the infrastructure files to understand what resources are deployed:

- For each costly service, find the IaC code that creates it
- Note resource configurations (CPU, memory, min instances, etc.)
- Identify scaling settings

### Step 6: Cost Attribution Analysis

For each significant cost category, trace it back to specific infrastructure:

#### Cloud Run Costs

```bash
# Get Cloud Run service configurations
echo ""
echo "Cloud Run Services:"
gcloud run services list --project="$PROJECT_ID" --format="table(name,region,spec.template.spec.containers[0].resources.limits.cpu,spec.template.spec.containers[0].resources.limits.memory)" 2>/dev/null
```

Map to IaC:
- Find service definitions in `modules/cloud_run.py`
- Note CPU/memory settings
- Check min/max instance counts

#### Firestore Costs

```bash
# Get Firestore usage stats (if available)
echo ""
echo "Firestore Stats:"
gcloud firestore databases describe --project="$PROJECT_ID" 2>/dev/null
```

Map to usage:
- Check index definitions in `modules/firestore.py`
- Review high-traffic endpoints in application code

#### Other Services

For each service with significant cost:
1. Identify what it is (Compute, Storage, Networking, etc.)
2. Find the IaC resource that creates it
3. Note current configuration

### Step 7: Identify Optimization Opportunities

Based on the cost data and IaC review, identify potential savings:

#### Cloud Run Optimizations
- **Min instances**: If services have `minInstances > 0`, they incur 24/7 costs
- **CPU allocation**: Check if `cpu: always` vs `cpu: on-demand`
- **Memory**: Over-provisioned memory costs more
- **Concurrency**: Higher concurrency = fewer instances needed

#### Firestore Optimizations
- **Indexes**: Unused composite indexes cost money
- **Read patterns**: Optimize queries to reduce document reads
- **Caching**: Add caching layer for frequently accessed data

#### General Optimizations
- **Committed use discounts**: For predictable workloads
- **Regional vs multi-regional**: Single region is cheaper
- **Resource scheduling**: Scale down during off-hours

### Step 8: Present Findings

Structure the final output:

```markdown
# GCP Billing Analysis - [PROJECT_ID]

**Period**: Last [N] days
**Total Spend**: $[X.XX]
**Daily Average**: $[X.XX]

## Daily Spend Trend

| Date | Cost | Change |
|------|------|--------|
| [date] | $X.XX | +/-X% |

[Note any anomalies or trends]

## Cost by Service

| Service | Cost | % of Total | Trend |
|---------|------|------------|-------|
| Cloud Run | $X.XX | XX% | [up/down/stable] |
| Firestore | $X.XX | XX% | [up/down/stable] |

## IaC Resource Mapping

### Cloud Run Services ($X.XX/month)

| Service | Monthly Cost | CPU | Memory | Min Instances | IaC Location |
|---------|--------------|-----|--------|---------------|--------------|
| [name] | $X.XX | [n] | [n]GB | [n] | `infrastructure/modules/cloud_run.py:123` |

### Firestore ($X.XX/month)

| Cost Type | Monthly Cost | Driver | IaC Location |
|-----------|--------------|--------|--------------|
| Document reads | $X.XX | [endpoint/collection] | [file:line] |
| Indexes | $X.XX | [n] composite indexes | `modules/firestore.py` |

### Other Services

[Similar tables for other significant costs]

## Optimization Opportunities

### Quick Wins (Implement Now)

1. **[Opportunity Name]** - Estimated savings: $X.XX/month
   - Current: [current config]
   - Recommended: [new config]
   - IaC change: [file and what to change]
   - Risk: [low/medium/high]

### Medium-Term (Plan)

1. **[Opportunity]** - $X.XX/month
   - Requires: [investigation/testing/architecture change]
   - Trade-offs: [what you give up]

### Long-Term (Consider)

1. **[Opportunity]** - $X.XX/month
   - Evaluation needed: [what to assess]

## Recommendations

1. **Immediate Action**: [top priority]
2. **This Week**: [second priority]
3. **Monitor**: [things to watch]

## Commands

# To implement a change:
/start backend optimize-[resource-name]

# To set up billing alerts:
gcloud billing budgets create --billing-account=[ACCOUNT] \
  --display-name="Monthly Budget" \
  --budget-amount=[AMOUNT]USD \
  --threshold-rule=percent=80,basis=current-spend

# To view cost breakdown in console:
# https://console.cloud.google.com/billing/[BILLING_ACCOUNT]/reports
```

## Fallback: No BigQuery Export

If BigQuery billing export is not configured:

1. Guide user to enable it (one-time setup)
2. Show billing console link for manual review
3. Use `gcloud billing` commands for what's available

```bash
echo ""
echo "=== MANUAL STEPS (BigQuery Export Not Configured) ==="
echo ""
echo "For detailed cost analysis, enable BigQuery billing export:"
echo ""
echo "1. Open Cloud Console: https://console.cloud.google.com/billing"
echo "2. Select billing account: $BILLING_ACCOUNT"
echo "3. Go to 'Billing export' in the left menu"
echo "4. Under 'Standard usage cost', click 'Edit settings'"
echo "5. Select or create a BigQuery dataset"
echo "6. Enable the export"
echo ""
echo "Export will start within 24 hours. Historical data is NOT backfilled."
echo ""
echo "For now, view costs in the console:"
echo "https://console.cloud.google.com/billing/$BILLING_ACCOUNT/reports?project=$PROJECT_ID"
```

## Common GCP Service to IaC Mappings

| GCP Service | Typical IaC Resource | What Drives Cost |
|-------------|---------------------|------------------|
| Cloud Run | `gcp.cloudrun.Service` | CPU, memory, min instances, requests |
| Firestore | (usage-based) | Document reads/writes, storage, indexes |
| Cloud Storage | `gcp.storage.Bucket` | Storage amount, operations, egress |
| Secret Manager | `gcp.secretmanager.Secret` | Number of secrets, access operations |
| Cloud Logging | (usage-based) | Log volume, retention |
| Artifact Registry | `gcp.artifactregistry.Repository` | Storage, egress |
| Cloud Scheduler | `gcp.cloudscheduler.Job` | Number of jobs (minimal cost) |
| Firebase Hosting | `gcp.firebase.HostingSite` | Bandwidth, storage |

## Decision Tree

```
START
  │
  ├─ BigQuery billing export exists?
  │   ├─ YES → Run detailed queries (Steps 3-6)
  │   └─ NO → Guide user to enable, show console link
  │
  ├─ Total spend > $100/month?
  │   ├─ YES → Full optimization analysis
  │   └─ NO → Quick summary, note scaling concerns
  │
  ├─ Single service > 50% of spend?
  │   ├─ YES → Deep dive on that service
  │   └─ NO → Balanced optimization across services
  │
  └─ Present recommendations ranked by ROI
```

## Notes

- BigQuery billing export takes up to 24 hours to start
- Historical data is NOT backfilled when you enable export
- Cost data in BigQuery can be 12-24 hours delayed
- For real-time spend, use the Billing Console
- Committed use discounts require 1 or 3-year commitments
