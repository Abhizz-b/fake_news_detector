import json
import os
from typing import Dict, Any, Optional
import streamlit as st


class UserConfigManager:
    """User Configuration Manager"""

    def __init__(self, user_id: int):
        """
        Initialize user configuration manager

        Args:
            user_id: User ID
        """
        self.user_id = user_id
        self.config_dir = "data/user_configs"
        self.config_file = os.path.join(self.config_dir, f"user_{user_id}.json")
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        os.makedirs(self.config_dir, exist_ok=True)

    def get_user_config(self) -> Dict[str, Any]:
        """
        Get user configuration

        Returns:
            User configuration dictionary
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Failed to read user configuration: {e}")
        return {}

    def save_user_config(self, config: Dict[str, Any]):
        """
        Save user configuration

        Args:
            config: User configuration dictionary
        """
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            st.toast("Configuration saved", icon="💾")
        except Exception as e:
            st.error(f"Failed to save user configuration: {e}")

    def update_user_config(self, updates: Dict[str, Any]):
        """
        Update user configuration

        Args:
            updates: Configuration items to update
        """
        current_config = self.get_user_config()
        current_config.update(updates)
        self.save_user_config(current_config)

    def get_model_config(self) -> Dict[str, Any]:
        """
        Get user model configuration

        Returns:
            Model configuration dictionary
        """
        return self.get_user_config().get("model_config", {})

    def save_model_config(self, model_config: Dict[str, Any]):
        """
        Save user model configuration

        Args:
            model_config: Model configuration dictionary
        """
        user_config = self.get_user_config()
        user_config["model_config"] = model_config
        self.save_user_config(user_config)

    def get_search_config(self) -> Dict[str, Any]:
        """
        Get user search configuration

        Returns:
            Search configuration dictionary
        """
        return self.get_user_config().get("search_config", {})

    def save_search_config(self, search_config: Dict[str, Any]):
        """
        Save user search configuration

        Args:
            search_config: Search configuration dictionary
        """
        user_config = self.get_user_config()
        user_config["search_config"] = search_config
        self.save_user_config(user_config)

    def get_default_config(self) -> Dict[str, Any]:
        """
        Get user default configuration

        Returns:
            Default configuration dictionary
        """
        return self.get_user_config().get("default_config", {})

    def save_default_config(self, default_config: Dict[str, Any]):
        """
        Save user default configuration

        Args:
            default_config: Default configuration dictionary
        """
        user_config = self.get_user_config()
        user_config["default_config"] = default_config
        self.save_user_config(user_config)

    def reset_config(self):
        """Reset user configuration"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            st.toast("Configuration reset", icon="🔄")
        except Exception as e:
            st.error(f"Failed to reset configuration: {e}")


def get_user_config_manager() -> Optional[UserConfigManager]:
    """
    Get the current user's configuration manager

    Returns:
        UserConfigManager instance, or None if user is not logged in
    """
    if hasattr(st.session_state, "user_id") and st.session_state.user_id:
        return UserConfigManager(st.session_state.user_id)
    return None