# Product photos for PalengkeWatch

Copied into the public repo `maleks-py/price-watch-action` from
`price-watch-app` `ci/product-photos/`. The private app repo was not readable
from this environment, so this README matches the workflow that was already
checked in (`product-photos.yml`, `scripts/build_product_media.mjs`,
`products.json`) plus the one-time setup those files expect.

Do not bundle these photos into the app. The app fetches `products-media.json`
at launch and loads each image from R2.

## What the Action does

On every push that touches `photos/**`, the script, the allowlist, or this
workflow (and on manual `workflow_dispatch`):

1. Normalizes `photos/<productId>.jpg` to a 384×384 JPEG (about 10–20 KB).
2. Uploads `dist/products/` to Cloudflare R2 under the `products/` prefix with
   `aws s3 sync` against R2's S3 endpoint.
3. Commits `products-media.json` when the manifest changes, so the app picks up
   new photos without a rebuild.

Filenames must match an id in `products.json`. Unknown names fail the job.

## Cost

$0 if you stay inside the free tiers.

- Public repo: GitHub Actions minutes are free.
- R2 free tier: 10 GB storage. Egress is always $0.
- Do **not** upload through the `price-watch-upload` Worker. It rate-limits
  10/hour and 50/day per IP and will throttle a bulk run.

## One-time setup

Cloudflare dashboard → R2 → Manage R2 API Tokens → Create API token with
**Object Read & Write** on bucket `price-watch-evidence`.

Repo → Settings → Secrets and variables → Actions:

| Kind | Name | Value |
| --- | --- | --- |
| Secret | `R2_ACCESS_KEY_ID` | Access Key ID from the token |
| Secret | `R2_SECRET_ACCESS_KEY` | Secret Access Key from the token |
| Secret | `R2_ACCOUNT_ID` | The `<id>` in `https://<id>.r2.cloudflarestorage.com` |
| Variable | `R2_BUCKET` | `price-watch-evidence` |
| Variable | `R2_PUBLIC_BASE` | `https://pub-fe5f70a35fe143a58b8eed518cf01e6a.r2.dev` |

Never paste those secrets into chat, issues, or commits.

## Adding a photo

Drop a file at `photos/<productId>.jpg` (also `.jpeg`, `.png`, or `.webp`).
Better input, better output: one subject, centered, plain or white background,
800 px or larger, no text, watermark, or props. Keep originals under about
400 KB.

Push to the default branch. The Action publishes the object and updates
`products-media.json`. Confirm with:

```text
https://raw.githubusercontent.com/maleks-py/price-watch-action/main/products-media.json
https://pub-fe5f70a35fe143a58b8eed518cf01e6a.r2.dev/products/<productId>.jpg?v=<hash>
```

## R2 and current AWS CLI

GitHub-hosted `ubuntu-latest` ships AWS CLI 2.36, which sends CRC64 checksum
headers by default. R2 rejects those. The workflow sets
`AWS_REQUEST_CHECKSUM_CALCULATION=when_required` and
`AWS_RESPONSE_CHECKSUM_VALIDATION=when_required`, which is the workaround
Cloudflare documents.
