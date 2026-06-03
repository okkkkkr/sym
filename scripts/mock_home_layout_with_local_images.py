import argparse
import asyncio
import mimetypes
import secrets
from pathlib import Path
from urllib import request

from tortoise import Tortoise

from app.controllers.home_layout import home_layout_controller
from app.schemas.home_layouts import HomeLayoutDraftSaveIn
from app.services.product_media_upload import product_media_upload_service
from app.settings import settings
from scripts.mock_home_layout import build_mock_payload


IMAGE_DIR = Path(settings.BASE_DIR) / "tmp" / "images"
SINGLE_IMAGE_NAME = "single_image.jpg"
MULTI_IMAGE_PATTERN = "multi_*.png"


def encode_multipart_formdata(fields: dict[str, str], file_path: Path, file_field: str = "file") -> tuple[bytes, str]:
    boundary = f"----CodexBoundary{secrets.token_hex(16)}"
    file_bytes = file_path.read_bytes()
    file_name = file_path.name
    content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    chunks: list[bytes] = []

    for key, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                str(value).encode(),
                b"\r\n",
            ]
        )

    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_name}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks), boundary


def upload_to_qiniu(file_path: Path) -> str:
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    credential = product_media_upload_service.create_upload_credentials(
        file_name=file_path.name,
        media_type="home_layout",
        content_type=content_type,
    )
    body, boundary = encode_multipart_formdata(
        {
            "token": credential["upload_token"],
            "key": credential["object_key"],
        },
        file_path=file_path,
    )
    req = request.Request(
        credential["upload_url"],
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with request.urlopen(req, timeout=max(30, int(settings.QINIU_UPLOAD_TIMEOUT_SECONDS or 300))) as response:
        status_code = getattr(response, "status", 200)
        if status_code < 200 or status_code >= 300:
            raise RuntimeError(f"Qiniu upload failed with status {status_code}")
        response.read()
    return credential["object_key"]


def module_image_plan(multi_images: list[Path]) -> dict[str, list[Path]]:
    return {
        "grid_4": [multi_images[0], multi_images[1], multi_images[2], multi_images[3]],
        "grid_2": [multi_images[4], multi_images[5]],
        "grid_8": [
            multi_images[0],
            multi_images[1],
            multi_images[2],
            multi_images[3],
            multi_images[4],
            multi_images[5],
            multi_images[6],
            multi_images[7],
        ],
        "carousel": [multi_images[6], multi_images[7], multi_images[0]],
        "horizontal_list": [multi_images[1], multi_images[2], multi_images[3], multi_images[4], multi_images[5]],
    }


def replace_images(payload: dict, single_image: Path, multi_images: list[Path]) -> dict:
    plan = module_image_plan(multi_images)
    single_uploaded_key = upload_to_qiniu(single_image)

    for module in payload["modules"]:
        if module["type"] == "single_image":
            module["items"][0]["image"] = single_uploaded_key
            continue

        source_images = plan[module["type"]]
        for item, source_image in zip(module["items"], source_images):
            item["image"] = upload_to_qiniu(source_image)
    return payload


async def main(apply_publish: bool) -> None:
    single_image = IMAGE_DIR / SINGLE_IMAGE_NAME
    multi_images = sorted(IMAGE_DIR.glob(MULTI_IMAGE_PATTERN))
    if not single_image.exists():
        raise FileNotFoundError(f"Missing single image: {single_image}")
    if len(multi_images) != 8:
        raise ValueError(f"Expected 8 multi images, found {len(multi_images)} in {IMAGE_DIR}")

    print("Uploading images to Qiniu by module...")

    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
    try:
        payload = replace_images(build_mock_payload(), single_image, multi_images)
        home_layout_payload = HomeLayoutDraftSaveIn(**payload)
        await home_layout_controller.save_draft(home_layout_payload)
        print("Home layout draft saved with uploaded image keys.")
        if apply_publish:
            published = await home_layout_controller.publish("home")
            print(
                "Home layout published.",
                f"version={published['version']}",
                f"modules={len(published['modules'])}",
            )
        else:
            print("Dry run finished. Re-run with --publish to publish the draft.")
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed home layout with local tmp/images assets uploaded to Qiniu.")
    parser.add_argument("--publish", action="store_true", help="Publish the generated home layout after saving draft.")
    args = parser.parse_args()
    asyncio.run(main(apply_publish=args.publish))
