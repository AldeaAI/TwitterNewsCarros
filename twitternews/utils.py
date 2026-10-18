from urllib.parse import urlparse

RESTRICTED_DOMAINS = [
    "eluniversal.com.mx", # @El_Universal_Mx
    "milenio.com", # @Milenio
    "infobae.com/mexico", #@infobaemexico
    "expansion.mx", # @ExpansionMx
    "elfinanciero.com.mx", # @ElFinanciero_Mx
    "reforma.com", # @Reforma
    "heraldodemexico.com.mx", # @HeraldodeMexico
    "motorpasion.com.mx", # @MotorpasionMex
    "autocosmos.com.mx", # @Autocosmos
    "autosactual.mx" # @autosactual
]

SOURCE_TWITTER_HANDLES = {
    "eluniversal.com.mx": "@El_Universal_Mx",
    "milenio.com": "@Milenio",
    "infobae.com/mexico": "@infobaemexico",
    "expansion.mx": "@ExpansionMx",
    "elfinanciero.com.mx": "@ElFinanciero_Mx",
    "reforma.com": "@Reforma",
    "heraldodemexico.com.mx": "@HeraldodeMexico",
    "motorpasion.com.mx": "@MotorpasionMex",
    "autocosmos.com.mx": "@Autocosmos",
    "autosactual.mx": "@autosactual",
}

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


def get_twitter_handle_for_url(url: str) -> str:
    """
    Returns the mapped Twitter handle for a source URL, or empty string if unknown.
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        path = parsed.path.strip("/").lower()
    except Exception:
        return ""

    # Exact domain + first path segment match (e.g., infobae.com/mexico)
    if path:
        first_segment = path.split("/")[0]
        domain_with_segment = f"{domain}/{first_segment}"
        if domain_with_segment in SOURCE_TWITTER_HANDLES:
            return SOURCE_TWITTER_HANDLES[domain_with_segment]

    # Exact domain match
    if domain in SOURCE_TWITTER_HANDLES:
        return SOURCE_TWITTER_HANDLES[domain]

    # Subdomain fallback match
    for source, handle in SOURCE_TWITTER_HANDLES.items():
        source_domain = source.split("/")[0]
        if domain == source_domain or domain.endswith(f".{source_domain}"):
            return handle

    return ""

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


# Tweet length: the writer aims for TWEET_TARGET_CHARS, but a tweet up to TWEET_MAX_CHARS is still
# accepted, since X's standard limit is 280.
TWEET_TARGET_CHARS = 245
TWEET_MAX_CHARS = 280

# Display names for the source hashtag, keyed by the domain's main label (no www, no TLD)
SOURCE_NAMES = {
    "motorpasion": "Motorpasion",
    "autocosmos": "Autocosmos",
    "autosactual": "AutosActual",
    "expansion": "Expansion",
    "elfinanciero": "ElFinanciero",
    "eluniversal": "ElUniversal",
    "milenio": "Milenio",
    "reforma": "Reforma",
    "heraldodemexico": "HeraldoDeMexico",
    "infobae": "Infobae",
}


def source_hashtag(url: str) -> str:
    """
    Hashtag with the outlet name for an article URL, e.g. '#Motorpasion'.
    Hashtags can't contain spaces, so names are written in CamelCase.
    Unknown sites fall back to their domain's main label, capitalized.
    """
    host = urlparse(url).netloc.lower().split(":")[0]
    labels = [part for part in host.split(".") if part != "www"]
    # Names like 'example.com.mx' keep the name before the second-level suffix
    if len(labels) >= 3 and labels[-2] in ("com", "co", "org", "net", "gob"):
        main = labels[-3]
    elif len(labels) >= 2:
        main = labels[-2]
    else:
        main = host
    return f"#{SOURCE_NAMES.get(main, main.capitalize())}"
