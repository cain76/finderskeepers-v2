"""
Web Scraping Service - Containerized web scraping service
"""

import asyncio
import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx
import requests
from bs4 import BeautifulSoup
from readability import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Web Scraping Service",
    description="Containerized web scraping service using Beautiful Soup and Readability",
    version="1.0.0"
)

# Request/Response models
class ScrapeRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    extract_content: bool = Field(default=True, description="Extract main content")
    extract_links: bool = Field(default=False, description="Extract all links")
    extract_images: bool = Field(default=False, description="Extract images")
    wait_for: Optional[str] = Field(default=None, description="CSS selector to wait for")
    timeout: int = Field(default=30, description="Timeout in seconds")
    user_agent: Optional[str] = Field(default=None, description="Custom user agent")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Custom headers")
    javascript: bool = Field(default=True, description="Execute JavaScript")
    
class ScrapeResponse(BaseModel):
    success: bool
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    html: Optional[str] = None
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    processing_time: Optional[float] = None

class BatchScrapeRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to scrape")
    extract_content: bool = Field(default=True, description="Extract main content")
    extract_links: bool = Field(default=False, description="Extract all links")
    extract_images: bool = Field(default=False, description="Extract images")
    timeout: int = Field(default=30, description="Timeout in seconds per URL")
    concurrent_limit: int = Field(default=3, description="Maximum concurrent requests")

class BatchScrapeResponse(BaseModel):
    success: bool
    total_urls: int
    successful_scrapes: int
    failed_scrapes: int
    results: List[ScrapeResponse]
    processing_time: float

# Service ready flag
service_ready = True

@app.on_event("startup")
async def startup_event():
    """Initialize the service on startup"""
    global service_ready
    try:
        logger.info("🚀 Initializing Web Scraping Service...")
        service_ready = True
        logger.info("✅ Web Scraping Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize service: {e}")
        service_ready = False
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global service_ready
    try:
        service_ready = False
        logger.info("✅ Web Scraping Service shut down")
    except Exception as e:
        logger.error(f"❌ Error shutting down service: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if service_ready else "unhealthy",
        "service": "web-scraping-service",
        "version": "1.0.0",
        "service_ready": service_ready,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest):
    """Scrape a single URL"""
    start_time = datetime.utcnow()
    
    if not service_ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        logger.info(f"🕷️ Scraping URL: {request.url}")
        
        # Prepare headers
        headers = {
            'User-Agent': request.user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Add custom headers if provided
        if request.headers:
            headers.update(request.headers)
        
        # Fetch the page
        async with httpx.AsyncClient(
            timeout=request.timeout,
            headers=headers,
            follow_redirects=True,
            verify=False
        ) as client:
            response = await client.get(request.url)
            response.raise_for_status()
            
            html_content = response.text
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ""
            
            # Extract main content using readability
            readable_content = ""
            if request.extract_content:
                try:
                    doc = Document(html_content)
                    readable_content = doc.summary()
                    # Parse the readable content to get clean text
                    readable_soup = BeautifulSoup(readable_content, 'html.parser')
                    readable_content = readable_soup.get_text().strip()
                except:
                    # Fallback to basic text extraction
                    readable_content = soup.get_text().strip()
            
            # Extract links
            links = []
            if request.extract_links:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http'):
                        links.append(href)
            
            # Extract images
            images = []
            if request.extract_images:
                for img in soup.find_all('img', src=True):
                    src = img['src']
                    if src.startswith('http'):
                        images.append(src)
            
            # Extract metadata
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Build response
            response_data = {
                "success": True,
                "url": request.url,
                "title": title,
                "processing_time": processing_time,
                "metadata": {
                    "word_count": len(readable_content.split()) if readable_content else 0,
                    "links_found": len(links),
                    "images_found": len(images),
                    "description": description,
                    "status_code": response.status_code
                }
            }
            
            # Add content if requested
            if request.extract_content:
                response_data["content"] = readable_content
                response_data["html"] = html_content
            
            # Add links if requested
            if request.extract_links:
                response_data["links"] = links
            
            # Add images if requested
            if request.extract_images:
                response_data["images"] = images
            
            logger.info(f"✅ Successfully scraped {request.url} in {processing_time:.2f}s")
            return ScrapeResponse(**response_data)
            
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"❌ Error scraping {request.url}: {str(e)}")
        return ScrapeResponse(
            success=False,
            url=request.url,
            error=str(e),
            processing_time=processing_time
        )

@app.post("/batch-scrape", response_model=BatchScrapeResponse)
async def batch_scrape_urls(request: BatchScrapeRequest):
    """Scrape multiple URLs concurrently"""
    start_time = datetime.utcnow()
    
    if not service_ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    logger.info(f"🕷️ Batch scraping {len(request.urls)} URLs")
    
    # Create individual scrape requests
    scrape_requests = [
        ScrapeRequest(
            url=url,
            extract_content=request.extract_content,
            extract_links=request.extract_links,
            extract_images=request.extract_images,
            timeout=request.timeout
        )
        for url in request.urls
    ]
    
    # Process with concurrency limit
    semaphore = asyncio.Semaphore(request.concurrent_limit)
    
    async def scrape_with_semaphore(scrape_req):
        async with semaphore:
            return await scrape_url(scrape_req)
    
    # Execute all scrapes concurrently
    results = await asyncio.gather(
        *[scrape_with_semaphore(req) for req in scrape_requests],
        return_exceptions=True
    )
    
    # Process results
    valid_results = []
    successful_scrapes = 0
    failed_scrapes = 0
    
    for result in results:
        if isinstance(result, Exception):
            failed_scrapes += 1
            valid_results.append(ScrapeResponse(
                success=False,
                url="unknown",
                error=str(result)
            ))
        else:
            valid_results.append(result)
            if result.success:
                successful_scrapes += 1
            else:
                failed_scrapes += 1
    
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(f"✅ Batch scraping completed: {successful_scrapes}/{len(request.urls)} successful in {processing_time:.2f}s")
    
    return BatchScrapeResponse(
        success=successful_scrapes > 0,
        total_urls=len(request.urls),
        successful_scrapes=successful_scrapes,
        failed_scrapes=failed_scrapes,
        results=valid_results,
        processing_time=processing_time
    )

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Web Scraping Service",
        "version": "1.0.0",
        "description": "Containerized web scraping service using Beautiful Soup and Readability",
        "endpoints": {
            "health": "/health",
            "scrape": "/scrape",
            "batch_scrape": "/batch-scrape",
            "docs": "/docs"
        },
        "status": "running",
        "ready": service_ready
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)