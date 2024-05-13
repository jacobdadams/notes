# Branch Protection

Branch name pattern should match the branch name you want to protect. Usuall ones are require PR, status check, and convo resolution.

# Environments

We usually have two environments for stuff that is "deployable" (pypi, gcp, etc): dev and prod. This allows us to have two separate sets of secrets and rules for separate deploy envs (gcp dev and prod, or just pypi prod).

## Protection rules

- Required reviewers: devs and Nathan

## Deployment branches

Set to protected branches. `main` should be protected as per Branch Protection above.

## GCP env secrets

These are the env secrets I've used for skids using cloud functions. Everything but Sendgrid gets auto-created after the terrraform env is created.

- IDENTITY_PROVIDER
- PROJECT_ID
- SENDGRID_API_KEY
- SERVICE_ACCOUNT_EMAIL (the function service account)
- STORAGE_BUCKET

# ServiceNow Business APM Stuff

# Actions

## Dependabot

Copy the dependabot .yml from another projection
