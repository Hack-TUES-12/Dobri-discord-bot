import logging
import os
import random
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv


BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "images"

# Load TOKEN (and other vars) from .env next to this file
load_dotenv(BASE_DIR / ".env")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("motivate_bot")


def get_random_image_path(images_dir: Path) -> Path:
    """Return a random supported image path from the given directory."""
    if not images_dir.exists() or not images_dir.is_dir():
        raise FileNotFoundError(f"Images directory was not found: {images_dir}")

    supported_extensions = {".jpg", ".jpeg", ".png"}
    image_files = [
        file_path
        for file_path in images_dir.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions
    ]

    if not image_files:
        raise FileNotFoundError(
            f"No supported image files were found in: {images_dir}"
        )

    return random.choice(image_files)


class MotivateBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        synced_commands = await self.tree.sync()
        logger.info("Synced %s slash command(s).", len(synced_commands))


bot = MotivateBot()


@bot.event
async def on_ready() -> None:
    if bot.user is not None:
        logger.info("Bot is ready as %s (ID: %s)", bot.user, bot.user.id)


@bot.tree.command(name="motivate", description="Send a random motivational image.")
async def motivate(interaction: discord.Interaction) -> None:
    await interaction.response.defer()

    try:
        image_path = get_random_image_path(IMAGES_DIR)
        discord_file = discord.File(image_path, filename=image_path.name)

        embed = discord.Embed(
            title="Motivation Boost",
            description="Here is a random motivational image for you.",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=f"attachment://{image_path.name}")

        await interaction.followup.send(embed=embed, file=discord_file)
    except FileNotFoundError as exc:
        logger.warning("Unable to send motivation image: %s", exc)
        await interaction.followup.send(
            "No motivational images are available right now. "
            "Please add `.jpg` or `.png` files to the `images` folder.",
            ephemeral=True,
        )
    except (OSError, discord.DiscordException) as exc:
        logger.exception("Failed to load or send image: %s", exc)
        await interaction.followup.send(
            "I found an image, but something went wrong while sending it.",
            ephemeral=True,
        )


def main() -> None:
    token = os.getenv("TOKEN")
    if not token:
        raise RuntimeError("Environment variable TOKEN is required.")

    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
