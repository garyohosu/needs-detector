import re


class Anonymizer:
    _LEGAL_TYPES = ("株式会社", "有限会社", "合同会社")
    _COMPANY_CHAR = re.compile(
        r"[A-Za-z0-9Ａ-Ｚａ-ｚ０-９一-龥々〆ヵヶぁ-んァ-ヶー・＆&.．]"
    )
    _HARD_BOUNDARY = frozenset("\r\n\t、。,:：;；!?！？「」『』（）()【】[]{}<>＜＞/\\")
    _CONTEXT_PREFIX = re.compile(
        r"^(?:顧客|取引先|勤務先|委託先|発注先|相手先|売却先|購入先|訪問先|"
        r"会社名|企業名|先方|今日|これ|当社|一般的)"
        r"(?:は|が|を|に|へ|で|と|の|な)?"
    )
    _POSTFIX_BOUNDARY = re.compile(
        r"(?:でした|です|ます)(?=$|[\s、。,:：;；!?！？])"
        r"|と(?=[A-Za-z0-9Ａ-Ｚａ-ｚ０-９一-龥々ぁ-んァ-ヶ])"
        r"|(?:へ|に|は|が|を|で)(?=(?:連絡|確認|勤務|依頼|相談|所属|訪問|"
        r"送付|提供|共有|報告|問い合わせ|入社|発注|委託|支払|利用|説明))"
    )
    _BRANCH_SUFFIX = re.compile(
        r"^(?P<base>.+?)(?P<branch>[一-龥々]{0,8}"
        r"(?:本社|本店|支店|支社|営業所|事業所|工場|研究所))$"
    )
    _GENERIC_COMPANY_NAMES = frozenset(
        {"制度", "法", "登記", "一覧", "情報", "概要", "について", "とは"}
    )
    _NON_COMPANY_AFTER = (
        "担当者",
        "社員",
        "従業員",
        "社長",
        "役員",
        "制度",
        "法",
        "登記",
        "一覧",
        "情報",
        "概要",
    )

    @classmethod
    def _is_company_char(cls, character: str) -> bool:
        return cls._COMPANY_CHAR.fullmatch(character) is not None

    @classmethod
    def _company_name_after(cls, text: str, start: int) -> tuple[str, int] | None:
        end = start
        while end < len(text):
            character = text[end]
            if character in cls._HARD_BOUNDARY:
                break
            if character not in " \u3000" and not cls._is_company_char(character):
                break
            end += 1

        raw = text[start:end].rstrip(" \u3000")
        spacing = raw[: len(raw) - len(raw.lstrip(" \u3000"))]
        name = raw[len(spacing) :]
        if not name:
            return None

        for boundary in cls._POSTFIX_BOUNDARY.finditer(name):
            if boundary.start() == 0:
                return None
            name = name[: boundary.start()].rstrip(" \u3000")
            end = start + len(spacing) + boundary.start()
            break

        normalized = cls._normalize_company_name(name, strip_branch=True)
        if normalized is None:
            return None
        return f"{spacing}{normalized}", end

    @classmethod
    def _company_name_before(cls, text: str, end: int) -> tuple[str, int] | None:
        start = end
        while start > 0:
            character = text[start - 1]
            if character in cls._HARD_BOUNDARY or character in " \u3000":
                break
            if not cls._is_company_char(character):
                break
            start -= 1

        name = text[start:end]
        previous_legal_ends = []
        for legal_type in cls._LEGAL_TYPES:
            position = name.rfind(legal_type)
            if position >= 0:
                previous_legal_ends.append(position + len(legal_type))
        previous_legal_end = max(previous_legal_ends, default=0)
        if previous_legal_end:
            start += previous_legal_end
            name = name[previous_legal_end:]
            connector = re.match(r"^(?:と|及び|および|または|・)", name)
            if connector:
                start += connector.end()
                name = name[connector.end() :]

        context = cls._CONTEXT_PREFIX.match(name)
        if context:
            start += context.end()
            name = name[context.end() :]

        for particle in reversed(list(re.finditer(r"[はがをにへでとの]", name))):
            left = name[: particle.start()]
            right = name[particle.end() :]
            if left and right and re.search(r"[A-Za-z0-9Ａ-Ｚａ-ｚ０-９ァ-ヶ]", right):
                start += particle.end()
                name = right
                break

        normalized = cls._normalize_company_name(name, strip_branch=False)
        if normalized is None:
            return None
        return normalized, start

    @classmethod
    def _orientation_after(cls, text: str, start: int) -> str:
        tail = text[start:].lstrip(" \u3000")
        if not tail or tail[0] in cls._HARD_BOUNDARY:
            return "suffix"
        if any(tail.startswith(word) for word in cls._GENERIC_COMPANY_NAMES):
            return "none"
        if any(tail.startswith(word) for word in cls._NON_COMPANY_AFTER):
            return "suffix"
        if cls._POSTFIX_BOUNDARY.match(tail):
            return "suffix"
        return "prefix"

    @classmethod
    def _normalize_company_name(cls, name: str, *, strip_branch: bool) -> str | None:
        name = name.strip(" \u3000")
        compact = name.replace(" ", "").replace("\u3000", "")
        if (
            not compact
            or len(compact) > 80
            or compact in cls._GENERIC_COMPANY_NAMES
            or any(legal_type in compact for legal_type in cls._LEGAL_TYPES)
            or not any(cls._is_company_char(character) for character in compact)
        ):
            return None

        if strip_branch:
            branch = cls._BRANCH_SUFFIX.fullmatch(name)
            if branch:
                base = branch.group("base").rstrip(" \u3000")
                # With an all-Kanji string there is no reliable boundary between
                # the trade name and a location name. Omit the candidate instead
                # of returning a misleading partial company name.
                if not base or re.fullmatch(r"[一-龥々]+", base):
                    return None
                name = base

        return name

    @classmethod
    def _scan_company_names(cls, text: str) -> list[str]:
        matches: list[tuple[int, str]] = []
        for legal_type in cls._LEGAL_TYPES:
            for legal_match in re.finditer(re.escape(legal_type), text):
                orientation = cls._orientation_after(text, legal_match.end())
                if orientation == "prefix":
                    after = cls._company_name_after(text, legal_match.end())
                    if after is not None:
                        name, _ = after
                        matches.append((legal_match.start(), f"{legal_type}{name}"))
                elif orientation == "suffix":
                    before = cls._company_name_before(text, legal_match.start())
                    if before is not None:
                        name, start = before
                        matches.append((start, f"{name}{legal_type}"))

        found: list[str] = []
        for _, candidate in sorted(matches, key=lambda item: item[0]):
            if candidate not in found:
                found.append(candidate)
        return found

    @classmethod
    def scan(cls, text: str) -> list[str]:
        found = []
        patterns = [
            r"[\w\.-]+@[\w\.-]+\.\w+",
            r"0\d{1,4}-\d{1,4}-\d{3,4}",
            r"\d{3}-\d{4}",
            r"https?://\S+",
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        ]

        for pattern in patterns:
            found.extend(match.group() for match in re.finditer(pattern, text))

        found.extend(cls._scan_company_names(text))
        return found
