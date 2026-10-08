import os
import yaml
from typing import Dict, Any, List

DEFAULT_CONFIG_PATH = os.path.join("config", "domains.yaml")

class DomainConfigManager:
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self._config_data: Dict[str, Any] = {}
        self._last_loaded_mtime: float = 0.0
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads or reloads the YAML configuration file."""
        if not os.path.exists(self.config_path):
            return {}
        
        mtime = os.path.getmtime(self.config_path)
        if mtime > self._last_loaded_mtime or not self._config_data:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self._config_data = data.get("domains", {})
                self._last_loaded_mtime = mtime

        return self._config_data

    def get_domains_dict(self) -> Dict[str, Any]:
        return self.load_config()

    def get_domain_keys(self) -> List[str]:
        return list(self.load_config().keys())

    def analyze_text_with_config(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text against the configurable YAML domains and sub-topics.
        """
        text_lower = text.lower()
        config = self.load_config()

        detected_domains = []
        detected_sub_topics = []

        for domain_key, domain_info in config.items():
            if domain_key == "general":
                continue
            
            # Check domain keywords
            domain_kw = domain_info.get("keywords", [])
            if any(kw.lower() in text_lower for kwkw in domain_kw for kw in [kwkw]):
                detected_domains.append(domain_key)

            # Check sub-topics keywords
            sub_topics = domain_info.get("sub_topics", {})
            for sub_key, sub_info in sub_topics.items():
                sub_kw = sub_info.get("keywords", [])
                if any(kw.lower() in text_lower for kwkw in sub_kw for kw in [kwkw]):
                    detected_sub_topics.append(sub_key)
                    if domain_key not in detected_domains:
                        detected_domains.append(domain_key)

        if not detected_domains:
            detected_domains = ["general"]

        primary_domain = detected_domains[0]

        return {
            "primary_domain": primary_domain,
            "domains": detected_domains,
            "sub_topics": detected_sub_topics
        }

domain_config_manager = DomainConfigManager()
