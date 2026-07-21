"""Upload an explicitly selected local checkpoint to the Hugging Face Hub."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import HfApi


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=Path(os.getenv("MODEL_DIR", "outputs/model")))
    parser.add_argument("--repo-id", default=os.getenv("HF_REPO_ID"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.repo_id:
        raise SystemExit("Provide --repo-id or set HF_REPO_ID before uploading.")
    if not args.model_dir.is_dir():
        raise SystemExit(f"Model directory does not exist: {args.model_dir}")
    api = HfApi()
    api.create_repo(repo_id=args.repo_id, repo_type="model", exist_ok=True)
    api.upload_folder(
        repo_id=args.repo_id,
        repo_type="model",
        folder_path=str(args.model_dir),
        commit_message="Upload Text-to-Cypher SmolLM2 checkpoint",
    )
    print(f"Uploaded {args.model_dir} to https://huggingface.co/{args.repo_id}")


if __name__ == "__main__":
    main()
