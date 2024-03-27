from typing import List


def get_social_urls(links: List[str]):
    def find_link(pattern: str, urls: List[str]):
        filtered_links = [url for url in urls if pattern in url]
        return None if len(filtered_links) == 0 else filtered_links[0]

    twitter = find_link('twitter.com/', links)
    telegram = find_link('t.me/', links)
    discord = find_link('discord.com/', links)
    linkedin = find_link('.linkedin.com/company', links)
    facebook = find_link('.facebook.com/', links)
    instagram = find_link('.instagram.com/', links)
    youtube = find_link('.youtube.com/', links)
    github = find_link('.github.com/', links)
    return {
        "twitter": twitter,
        "telegram": telegram,
        "discord": discord,
        "linkedin": linkedin,
        "facebook": facebook,
        "instagram": instagram,
        "youtube": youtube,
        "github": github
    }
