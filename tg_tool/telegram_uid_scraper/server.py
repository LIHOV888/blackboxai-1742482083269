"""
Backend server for the Telegram UID Scraper dashboard
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from aiohttp import web
from aiohttp.web import Request, Response, FileResponse
from aiohttp_cors import setup as cors_setup, ResourceOptions

from .logger import Logger
from .scraper import TelegramScraper
from .types import Stats, TelegramUID


class DashboardServer:
    """
    Handles the web server for the dashboard, providing API endpoints
    for real-time statistics and data
    """

    def __init__(
        self,
        scraper: TelegramScraper,
        logger: Logger,
        host: str = "localhost",
        port: int = 8000
    ):
        self.scraper = scraper
        self.logger = logger
        self.host = host
        self.port = port
        self.app = web.Application()
        self.dashboard_path = str(Path(__file__).parent.parent / "dashboard")
        self._setup_routes()
        self._setup_cors()
        self._recent_uids: List[TelegramUID] = []
        self._max_recent_uids = 100

    def _setup_routes(self):
        """Configure API routes and static file serving"""
        # API routes
        self.app.router.add_get("/api/stats", self.get_stats)
        self.app.router.add_get("/api/logs", self.get_logs)
        self.app.router.add_get("/api/uids", self.get_uids)

        # Static file routes
        self.app.router.add_get("/", self.serve_index)
        self.app.router.add_get("/app.js", self.serve_js)
        self.app.router.add_static("/", path=self.dashboard_path)

    def _setup_cors(self):
        """Configure CORS for API endpoints"""
        cors = cors_setup(self.app, defaults={
            "*": ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Configure CORS for all routes
        for route in list(self.app.router.routes()):
            cors.add(route)

    async def serve_index(self, request: Request) -> FileResponse:
        """Serve the index.html file"""
        self.logger.info("Serving index.html")
        return FileResponse(Path(self.dashboard_path) / "index.html")

    async def serve_js(self, request: Request) -> FileResponse:
        """Serve the app.js file"""
        self.logger.info("Serving app.js")
        return FileResponse(Path(self.dashboard_path) / "app.js")

    async def get_stats(self, request: Request) -> Response:
        """
        Handle /api/stats endpoint
        Returns current scraping statistics
        """
        try:
            stats = self.scraper.get_stats()
            return web.json_response({
                "total_processed": stats.total_processed,
                "successful_scrapes": stats.successful_scrapes,
                "failed_scrapes": stats.failed_scrapes,
                "current_rate": stats.current_rate,
                "bandwidth_used": stats.bandwidth_used,
                "estimated_time_remaining": stats.estimated_time_remaining,
                "auto_add_stats": stats.auto_add_stats,
                "start_time": stats.start_time
            })
        except Exception as e:
            self.logger.error(f"Failed to get stats: {str(e)}")
            return web.json_response({
                "error": f"Failed to get stats: {str(e)}"
            }, status=500)

    async def get_logs(self, request: Request) -> Response:
        """
        Handle /api/logs endpoint
        Returns recent log entries
        """
        try:
            # Get query parameters
            limit = int(request.query.get("limit", "100"))
            level = request.query.get("level", "ALL")
            
            # Get logs from logger
            logs = await self.logger.get_recent_logs(limit)
            
            # Filter by level if specified
            if level != "ALL":
                logs = [log for log in logs if log["level"] == level]
            
            return web.json_response(logs)
        except Exception as e:
            self.logger.error(f"Failed to get logs: {str(e)}")
            return web.json_response({
                "error": f"Failed to get logs: {str(e)}"
            }, status=500)

    async def get_uids(self, request: Request) -> Response:
        """
        Handle /api/uids endpoint
        Returns recently scraped UIDs
        """
        try:
            # Get query parameters
            limit = int(request.query.get("limit", "10"))
            
            # Return most recent UIDs
            return web.json_response(self._recent_uids[:limit])
        except Exception as e:
            self.logger.error(f"Failed to get UIDs: {str(e)}")
            return web.json_response({
                "error": f"Failed to get UIDs: {str(e)}"
            }, status=500)

    def add_uid(self, uid: TelegramUID):
        """Add a new UID to the recent list"""
        self._recent_uids.insert(0, uid)
        if len(self._recent_uids) > self._max_recent_uids:
            self._recent_uids.pop()

    async def start(self):
        """Start the web server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        
        try:
            await site.start()
            self.logger.info(
                f"Dashboard server started at http://{self.host}:{self.port}"
            )
        except Exception as e:
            self.logger.error(f"Failed to start dashboard server: {str(e)}")
            raise

    async def stop(self):
        """Stop the web server"""
        await self.app.shutdown()
        self.logger.info("Dashboard server stopped")


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)