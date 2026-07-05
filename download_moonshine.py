from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Sanjidh090/moonshine-base-bn",
    local_dir="./models/moonshine-base-bn",
    local_dir_use_symlinks=False
)

print("Moonshine downloaded successfully!")