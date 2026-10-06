import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_DIR = Path(__file__).resolve().parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"
APP_NAME = "Little Day"
APP_PATH = DIST_DIR / f"{APP_NAME}.app"


# ---------------------------------------------------------
# Create Little Day icon
# ---------------------------------------------------------

def create_icon():
    icon_path = PROJECT_DIR / "little_day_icon.png"

    size = 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = int(size * 0.035)
    radius = int(size * 0.22)

    # Rounded macOS-style outer shape
    draw.rounded_rectangle(
        (
            margin,
            margin,
            size - margin - 1,
            size - margin - 1,
        ),
        radius=radius,
        fill="#FFF9EC",
    )

    # Soft inner pastel circle
    center = size // 2
    circle_radius = int(size * 0.30)

    draw.ellipse(
        (
            center - circle_radius,
            center - circle_radius,
            center + circle_radius,
            center + circle_radius,
        ),
        fill="#D8EADF",
    )

    # Cute little sun
    sun_radius = int(size * 0.18)

    draw.ellipse(
        (
            center - sun_radius,
            center - sun_radius,
            center + sun_radius,
            center + sun_radius,
        ),
        fill="#F5D7C8",
    )

    # Face
    eye_radius = int(size * 0.018)

    left_eye_x = center - int(size * 0.07)
    right_eye_x = center + int(size * 0.07)
    eye_y = center - int(size * 0.025)

    draw.ellipse(
        (
            left_eye_x - eye_radius,
            eye_y - eye_radius,
            left_eye_x + eye_radius,
            eye_y + eye_radius,
        ),
        fill="#39352F",
    )

    draw.ellipse(
        (
            right_eye_x - eye_radius,
            eye_y - eye_radius,
            right_eye_x + eye_radius,
            eye_y + eye_radius,
        ),
        fill="#39352F",
    )

    # Smile
    smile_box = (
        center - int(size * 0.08),
        center - int(size * 0.005),
        center + int(size * 0.08),
        center + int(size * 0.09),
    )

    draw.arc(
        smile_box,
        start=15,
        end=165,
        fill="#39352F",
        width=int(size * 0.015),
    )

    image.save(icon_path)

    print("✓ Created Little Day icon")
    return icon_path


# ---------------------------------------------------------
# Clean previous build
# ---------------------------------------------------------

def clean():
    # Remove previous PyInstaller build contents
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    if DIST_DIR.exists():
        for item in DIST_DIR.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink()
            except OSError as error:
                print(f"Warning: could not remove {item}: {error}")

    spec_file = PROJECT_DIR / f"{APP_NAME}.spec"

    if spec_file.exists():
        try:
            spec_file.unlink()
        except OSError as error:
            print(f"Warning: could not remove spec file: {error}")

    print("✓ Cleaned previous build")


# ---------------------------------------------------------
# Build application
# ---------------------------------------------------------

def build_app(icon_path):
    command = [
        "python",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--icon",
        str(icon_path),
        "--collect-all",
        "qtawesome",
        "--collect-all",
        "google.genai",
        "main.py",
    ]

    print("\nBuilding Little Day...\n")

    subprocess.run(
        command,
        cwd=PROJECT_DIR,
        check=True,
    )

    print("\n✓ PyInstaller build complete")


# ---------------------------------------------------------
# Local code signing
# ---------------------------------------------------------

def sign_app():
    print("\nSigning Little Day.app...")

    command = [
        "codesign",
        "--force",
        "--deep",
        "--sign",
        "-",
        str(APP_PATH),
    ]

    subprocess.run(
        command,
        check=True,
    )

    print("✓ App signed locally")


# ---------------------------------------------------------
# Verify bundle
# ---------------------------------------------------------

def verify_app():
    print("\nVerifying application bundle...\n")

    subprocess.run(
        [
            "codesign",
            "--verify",
            "--deep",
            "--strict",
            "--verbose=2",
            str(APP_PATH),
        ],
        check=True,
    )

    print("\n✓ Application verification passed")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    print("=" * 40)
    print("       Building Little Day")
    print("=" * 40)

    icon_path = create_icon()

    clean()

    build_app(icon_path)

    if not APP_PATH.exists():
        raise RuntimeError(
            f"Build completed but {APP_PATH} was not created."
        )

    sign_app()

    verify_app()

    print("\n" + "=" * 40)
    print("      Little Day built successfully!")
    print("=" * 40)

    print(f"\nApp:")
    print(APP_PATH)


if __name__ == "__main__":
    main()