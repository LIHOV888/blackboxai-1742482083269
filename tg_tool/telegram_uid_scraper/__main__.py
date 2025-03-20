"""
Main entry point for the Telegram UID Scraper
"""

import asyncio
import signal
import sys
from typing import Optional

from .cli import parse_args, create_configs
from .logger import Logger
from .scraper import TelegramScraper
from .server import DashboardServer
from .ui import TelegramScraperUI


async def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_args()
    
    try:
        # Create configurations
        (
            scraper_config,
            filter_config,
            log_config,
            ui_config,
            export_config,
            dashboard_config
        ) = create_configs(args)

        # Initialize logger
        logger = Logger(log_config)
        logger.info("Starting Telegram UID Scraper")

        # Initialize UI
        ui = TelegramScraperUI(ui_config)
        await ui.start()

        # Initialize scraper
        scraper = TelegramScraper(
            scraper_config,
            logger,
            filter_config
        )

        # Initialize dashboard if enabled
        dashboard: Optional[DashboardServer] = None
        if dashboard_config.enabled:
            dashboard = DashboardServer(
                scraper,
                logger,
                host="0.0.0.0",  # Changed from localhost to allow external access
                port=8000
            )
            await dashboard.start()
            logger.info(
                f"Dashboard available at http://localhost:8000"
            )

        # Handle shutdown gracefully
        async def shutdown(sig: signal.Signals):
            logger.info(f"Received signal {sig.name}, shutting down...")
            if dashboard:
                await dashboard.stop()
            await scraper.stop()
            await ui.stop()
            sys.exit(0)

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(s))
            )

        # Start scraping
        scraped_uids = []
        async with scraper:
            async for uid in scraper.scrape_all():
                scraped_uids.append(uid)
                await ui.update(uid, scraper.get_stats())
                if dashboard:
                    dashboard.add_uid(uid)

        # Export results
        if scraped_uids:
            if export_config.format == "json":
                await logger.export_json(scraped_uids, export_config.output_path)
            else:  # csv
                await logger.export_csv(scraped_uids, export_config.output_path)

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

    finally:
        logger.info("Scraping completed")


def run():
    """Entry point for the CLI"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    run()