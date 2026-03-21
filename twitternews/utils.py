from urllib.parse import urlparse

RESTRICTED_DOMAINS = [
    "eluniversal.com.mx",
    "milenio.com",
    "infobae.com/mexico",
    "expansion.mx",
    "elfinanciero.com.mx",
    "reforma.com",
    "heraldodemexico.com.mx",
    "motorpasion.com.mx",
    "autocosmos.com.mx",
    "autosactual.mx"
]

# Add specific URLs to this set to blacklist them exactly
BLACKLISTED_URLS = {
    # "https://www.motorpasion.com.mx",
    # "https://www.autocosmos.com.mx",
    # "https://www.autosactual.mx"
}

BLACKLISTED_URL_PREFIXES = [
    # "https://www.motorpasion.com.mx",
    # "https://www.autocosmos.com.mx",
    # "https://www.autosactual.mx"
]

def is_blacklisted(url: str) -> bool:
    """
    True if URL is a root domain, a restricted domain with exactly one path segment,
    matches a specifically blacklisted URL, starts with a blacklisted prefix,
    or (for elcolombiano.com) contains '/meta/' in the path.
    """
    # Check for exact URL blacklist
    if url in BLACKLISTED_URLS:
        return True

    # Check for prefix blacklist (e.g., all subpages under a path)
    for prefix in BLACKLISTED_URL_PREFIXES:
        if url.startswith(prefix):
            return True

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        clean_path = parsed.path.strip("/")


        if not clean_path:
            return True

        if any(d in domain for d in RESTRICTED_DOMAINS):
            if len(clean_path.split("/")) == 1:
                return True

        # Blacklist URLs containing 'AMP' (case-insensitive)
        if "amp" in url.lower():
            return True

        return False
    except Exception:
        return False
