from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="facebook/nllb-200-distilled-600M",
    local_dir="./models/nllb-200-distilled-600M",
    local_dir_use_symlinks=False
)

print("NLLB downloaded successfully!")