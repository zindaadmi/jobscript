#!/usr/bin/env python3
import os
import sys
import time
import json
import csv
import random
import pathlib
from contextlib import contextmanager
from typing import List, Optional, Tuple, Dict

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import box
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Page, BrowserContext


console = Console()


def env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    return value if value is not None and value != "" else default


def sleep_human(min_s: float = 0.6, max_s: float = 1.6) -> None:
    time.sleep(random.uniform(min_s, max_s))


def ensure_dir(path: str) -> None:
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def write_csv(path: str, rows: List[Dict[str, str]], headers: List[str]) -> None:
    is_new = not os.path.exists(path)
    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if is_new:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def print_summary(applied: List[Dict[str, str]], shortlisted: List[Dict[str, str]]) -> None:
    if applied:
        t = Table(title="Applied", box=box.SIMPLE)
        t.add_column("Title")
        t.add_column("Company")
        t.add_column("Link")
        for r in applied:
            t.add_row(r.get("title", ""), r.get("company", ""), r.get("link", ""))
        console.print(t)
    if shortlisted:
        t = Table(title="Shortlisted for manual apply", box=box.SIMPLE)
        t.add_column("Title")
        t.add_column("Company")
        t.add_column("Reason")
        t.add_column("Link")
        for r in shortlisted:
            t.add_row(r.get("title", ""), r.get("company", ""), r.get("reason", ""), r.get("link", ""))
        console.print(t)


def find_first_selector(page: Page, selectors: List[str], timeout_ms: int = 4000) -> Optional[str]:
    for sel in selectors:
        try:
            page.wait_for_selector(sel, state="visible", timeout=timeout_ms)
            return sel
        except PlaywrightTimeoutError:
            continue
    return None


class NaukriAutoApply:
    def __init__(
        self,
        context: BrowserContext,
        headless: bool,
        output_dir: str,
        resume_path: Optional[str],
        min_exp: int,
        delay_range: Tuple[float, float],
    ) -> None:
        self.context = context
        self.headless = headless
        self.output_dir = output_dir
        self.resume_path = resume_path
        self.min_exp = min_exp
        self.delay_min, self.delay_max = delay_range
        self.applied_rows: List[Dict[str, str]] = []
        self.shortlisted_rows: List[Dict[str, str]] = []

    def _human_sleep(self) -> None:
        sleep_human(self.delay_min, self.delay_max)

    def login(self, email: str, password: str) -> None:
        page = self.context.new_page()
        page.set_default_timeout(12000)
        with console.status("Navigating to login page..."):
            page.goto("https://www.naukri.com/nlogin/login")
        self._human_sleep()

        # Handle possible legacy login page variants
        email_selectors = [
            'input[name="emailId"]',
            'input#usernameField',
            'input[name="username"]',
            'input[placeholder*="Email ID"]',
            'input[type="text"]',
        ]
        pwd_selectors = [
            'input[name="password"]',
            'input#passwordField',
            'input[type="password"]',
        ]
        login_btn_selectors = [
            'button[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
        ]

        sel_email = find_first_selector(page, email_selectors, 7000)
        if not sel_email:
            # Sometimes Naukri shows a unified login form after redirect
            page.goto("https://www.naukri.com")
            self._human_sleep()
            # Try opening login from nav
            try:
                page.click('a:has-text("Login")', timeout=5000)
                self._human_sleep()
            except Exception:
                pass
            sel_email = find_first_selector(page, email_selectors, 7000)

        if not sel_email:
            raise RuntimeError("Could not find email field on login page.")

        page.fill(sel_email, email)
        self._human_sleep()
        sel_pwd = find_first_selector(page, pwd_selectors, 7000)
        if not sel_pwd:
            raise RuntimeError("Could not find password field on login page.")
        page.fill(sel_pwd, password)
        self._human_sleep()

        sel_login = find_first_selector(page, login_btn_selectors, 7000)
        if not sel_login:
            raise RuntimeError("Could not find login button on login page.")
        page.click(sel_login)
        self._human_sleep()

        # Dismiss potential popups (cookie, notification)
        for sel in [
            'button:has-text("Got it")',
            'button:has-text("OK")',
            'button:has-text("Accept")',
            'button#onetrust-accept-btn-handler',
        ]:
            try:
                page.click(sel, timeout=3000)
                self._human_sleep()
            except Exception:
                pass

        # Heuristic: wait for avatar or user menu
        try:
            page.wait_for_selector('a[title*="View Profile"], img[alt*="profile"]', timeout=15000)
            console.log("Logged in to Naukri successfully")
        except PlaywrightTimeoutError:
            console.print("[yellow]Login might not have completed; continuing anyway.[/yellow]")

        page.close()

    def _open_search(self, query: str, locations: Optional[List[str]]) -> Page:
        page = self.context.new_page()
        page.set_default_timeout(15000)
        console.log(f"Searching for jobs: {query}")
        page.goto("https://www.naukri.com/")
        self._human_sleep()

        # Enter query
        skill_selectors = [
            'input#qsb-keyskill-sugg',
            'input[placeholder*="Skills"]',
            'input[aria-label*="Skills"]',
        ]
        sel_skill = find_first_selector(page, skill_selectors, 6000)
        if not sel_skill:
            # Fallback to direct URL query
            safe_q = query.replace(" ", "%20")
            page.goto(f"https://www.naukri.com/{safe_q}-jobs?k={safe_q}")
        else:
            page.click(sel_skill)
            page.fill(sel_skill, query)

            # Fill location if provided
            if locations and len(locations) > 0:
                loc_selectors = [
                    'input#qsb-location-sugg',
                    'input[placeholder*="Location"]',
                ]
                sel_loc = find_first_selector(page, loc_selectors, 2000)
                if sel_loc:
                    page.fill(sel_loc, ", ".join(locations))
                    self._human_sleep()

            # Submit search
            for sel in ['button.qsbSubmit', 'button[type="submit"]', 'span.qsbSubmit']:  # variants
                try:
                    page.click(sel, timeout=3000)
                    break
                except Exception:
                    continue

        self._human_sleep()

        # Apply experience filter if available
        try:
            # Open experience filter panel if exists
            exp_filter_triggers = [
                'span:has-text("Experience")',
                'div:has-text("Experience")',
                'button:has-text("Experience")',
            ]
            trigger = find_first_selector(page, exp_filter_triggers, 4000)
            if trigger:
                page.click(trigger)
                self._human_sleep()
            # Try to set minimum years
            # Some UIs have two inputs or slider; we try input first
            for sel in [
                'input[placeholder="Min"]',
                'input[name="experienceMin"]',
                'input[aria-label*="Min experience"]',
            ]:
                try:
                    page.fill(sel, str(self.min_exp))
                    self._human_sleep()
                    break
                except Exception:
                    continue
            # Apply/submit filters
            for sel in [
                'button:has-text("Apply")',
                'button:has-text("Done")',
                'button:has-text("OK")',
            ]:
                try:
                    page.click(sel, timeout=2000)
                    break
                except Exception:
                    continue
        except Exception:
            pass

        # Wait for results
        try:
            page.wait_for_selector('[data-job-id], article:has(button:has-text("Apply"))', timeout=12000)
        except PlaywrightTimeoutError:
            console.print("[yellow]No results loaded for this query yet.[/yellow]")
        return page

    def _extract_cards(self, page: Page) -> List[Tuple[str, str, str]]:
        # Returns list of (title, company, link)
        cards: List[Tuple[str, str, str]] = []
        # Try multiple job card selectors
        card_selectors = [
            'article',
            'div.listingCard',
            'div#root div[class*="JobCard"]',
        ]
        selector = None
        for sel in card_selectors:
            try:
                page.wait_for_selector(f"{sel} >> text=Apply", timeout=4000)
                selector = sel
                break
            except Exception:
                continue
        if selector is None:
            selector = card_selectors[0]

        elements = page.query_selector_all(selector)
        for el in elements:
            try:
                title_el = el.query_selector('a[title], a[href*="/job-"], a[href*="/jobs/"], a')
                title = (title_el.inner_text().strip() if title_el else "").replace("\n", " ")
                link = title_el.get_attribute("href") if title_el else None
                if link and not link.startswith("http"):
                    link = f"https://www.naukri.com{link}"
                comp_el = el.query_selector('a[title*="Company"], span.comp-name, div.comp-name, a.subTitle, a#companyName')
                company = comp_el.inner_text().strip().replace("\n", " ") if comp_el else ""
                if link and title:
                    cards.append((title, company, link))
            except Exception:
                continue
        return cards

    def _shortlist_on_page(self, page: Page) -> bool:
        # Try to click shortlist/save button on job detail page
        btn_selectors = [
            'button:has-text("Shortlist")',
            'button:has-text("Save")',
            'span:has-text("Shortlist")',
        ]
        for sel in btn_selectors:
            try:
                page.click(sel, timeout=2000)
                self._human_sleep()
                return True
            except Exception:
                continue
        return False

    def _detect_external_or_detailed_apply(self, before_urls: List[str]) -> str:
        # Returns reason string if needs manual, empty if OK for auto-apply
        # If any new page with non-naukri domain opens, it's external
        for p in self.context.pages:
            url = p.url
            if url.startswith("about:blank") or url in before_urls:
                continue
            if "naukri.com" not in url:
                return "External apply (company site)"
        # Otherwise, check for multiple inputs indicating detailed form
        try:
            active = self.context.pages[-1]
            inputs = active.query_selector_all("form input, form select, form textarea")
            if len(inputs) >= 3:
                return "Detailed form requires manual entry"
        except Exception:
            pass
        return ""

    def _attempt_apply_on_detail(self, page: Page, title: str, company: str, link: str) -> bool:
        # Try to apply
        apply_selectors = [
            'button:has-text("Apply")',
            'a:has-text("Apply")',
        ]
        # Sometimes there are multiple buttons; avoid ones that say 'Apply on company site'
        for sel in apply_selectors:
            candidates = page.query_selector_all(sel)
            for btn in candidates:
                try:
                    txt = btn.inner_text().strip().lower()
                except Exception:
                    txt = ""
                if "company" in txt or "site" in txt or "external" in txt:
                    continue
                try:
                    before_urls = [p.url for p in self.context.pages]
                    btn.click()
                    self._human_sleep()
                    reason = self._detect_external_or_detailed_apply(before_urls)
                    if reason:
                        # Shortlist instead of applying
                        self._shortlist_on_page(page)
                        self.shortlisted_rows.append({
                            "title": title,
                            "company": company,
                            "link": link,
                            "reason": reason,
                        })
                        return False
                    # Look for success indicator
                    success_texts = ["Applied", "Application submitted", "Thanks for applying"]
                    for st in success_texts:
                        try:
                            page.wait_for_selector(f'text={st}', timeout=4000)
                            self.applied_rows.append({
                                "title": title,
                                "company": company,
                                "link": link,
                            })
                            return True
                        except Exception:
                            continue
                    # If no explicit success but still on naukri and no more inputs, assume applied
                    self.applied_rows.append({
                        "title": title,
                        "company": company,
                        "link": link,
                    })
                    return True
                except Exception:
                    continue
        # If no apply button at all, shortlist
        self._shortlist_on_page(page)
        self.shortlisted_rows.append({
            "title": title,
            "company": company,
            "link": link,
            "reason": "No direct Apply button found",
        })
        return False

    def search_and_apply(
        self,
        queries: List[str],
        locations: Optional[List[str]],
        max_jobs: int,
    ) -> None:
        visited: set = set()
        total_processed = 0
        for query in queries:
            page = self._open_search(query, locations)
            self._human_sleep()
            cards = self._extract_cards(page)
            if not cards:
                # Try to scroll to load more
                for _ in range(5):
                    try:
                        page.mouse.wheel(0, 1200)
                        self._human_sleep()
                    except Exception:
                        break
                cards = self._extract_cards(page)

            for title, company, link in cards:
                if link in visited:
                    continue
                visited.add(link)
                total_processed += 1
                console.log(f"Processing: {title} | {company}")

                # Open detail in new tab to avoid losing list
                detail = self.context.new_page()
                try:
                    detail.goto(link, wait_until="domcontentloaded")
                except Exception:
                    try:
                        detail.goto(link)
                    except Exception:
                        self.shortlisted_rows.append({
                            "title": title,
                            "company": company,
                            "link": link,
                            "reason": "Failed to open job detail",
                        })
                        detail.close()
                        continue
                self._human_sleep()

                # Try quick apply on detail page
                try:
                    self._attempt_apply_on_detail(detail, title, company, link)
                except Exception as e:
                    console.print(f"[yellow]Apply attempt failed: {e}[/yellow]")
                    try:
                        self._shortlist_on_page(detail)
                    except Exception:
                        pass
                    self.shortlisted_rows.append({
                        "title": title,
                        "company": company,
                        "link": link,
                        "reason": "Error during apply",
                    })
                finally:
                    detail.close()

                # Stop if reached max_jobs
                if 0 < max_jobs <= (len(self.applied_rows) + len(self.shortlisted_rows)):
                    page.close()
                    return

            page.close()

    def save_outputs(self) -> Tuple[str, str]:
        ensure_dir(self.output_dir)
        applied_path = os.path.join(self.output_dir, "applied.csv")
        shortlist_path = os.path.join(self.output_dir, "shortlist.csv")
        write_csv(applied_path, self.applied_rows, ["title", "company", "link"])
        write_csv(shortlist_path, self.shortlisted_rows, ["title", "company", "reason", "link"])
        return applied_path, shortlist_path


def parse_args(argv: List[str]):
    import argparse

    parser = argparse.ArgumentParser(description="Auto-apply to Naukri jobs and shortlist externals.")
    parser.add_argument(
        "--queries",
        "-q",
        nargs="+",
        default=[
            "backend developer java",
            "java spring boot",
            "backend java",
        ],
        help="Job search queries to run",
    )
    parser.add_argument("--locations", "-l", nargs="*", default=None, help="Preferred locations")
    parser.add_argument("--min-exp", type=int, default=3, help="Minimum years of experience filter")
    parser.add_argument("--max-jobs", type=int, default=40, help="Stop after this many jobs processed")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--delay-min", type=float, default=0.8, help="Min human delay seconds")
    parser.add_argument("--delay-max", type=float, default=1.8, help="Max human delay seconds")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join(str(pathlib.Path.cwd()), "output"),
        help="Directory to store CSV outputs",
    )
    parser.add_argument("--resume", type=str, default=None, help="Path to resume file if needed")

    args = parser.parse_args(argv)
    return args


def main(argv: List[str]) -> int:
    load_dotenv()
    args = parse_args(argv)

    naukri_email = env("NAUKRI_EMAIL")
    naukri_password = env("NAUKRI_PASSWORD")
    if not naukri_email or not naukri_password:
        console.print("[red]Please set NAUKRI_EMAIL and NAUKRI_PASSWORD in environment or .env[/red]")
        return 2

    resume_path = args.resume or env("RESUME_PATH")
    if resume_path and not os.path.isfile(resume_path):
        console.print(f"[yellow]Resume file not found at {resume_path}. Continuing without upload.[/yellow]")
        resume_path = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        # Reduce detection
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        runner = NaukriAutoApply(
            context=context,
            headless=args.headless,
            output_dir=args.output_dir,
            resume_path=resume_path,
            min_exp=args.min_exp,
            delay_range=(args.delay_min, args.delay_max),
        )

        runner.login(naukri_email, naukri_password)
        runner.search_and_apply(args.queries, args.locations, args.max_jobs)

        applied_path, shortlist_path = runner.save_outputs()
        browser.close()

    print_summary(runner.applied_rows, runner.shortlisted_rows)
    console.print(f"[green]Applied list saved to:[/green] {applied_path}")
    console.print(f"[yellow]Shortlist saved to:[/yellow] {shortlist_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

