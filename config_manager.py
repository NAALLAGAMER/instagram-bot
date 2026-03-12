"""
Configuration Manager - Handles all configuration without .env file
"""

import os
import json
from datetime import datetime
from loguru import logger

class ConfigManager:
    def __init__(self, config_file='bot_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            'instagram_username': '',
            'instagram_password': '',
            'telegram_token': '',
            'telegram_bot_username': '',
            'admin_user_id': '',
            'check_interval': 60,
            'max_replies_per_hour': 50,
            'flirt_level': 'moderate',
            'auto_like': True,
            'created_at': None,
            'updated_at': None
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with default config
                    default_config.update(loaded_config)
                    logger.info("✅ Configuration loaded from file")
            except Exception as e:
                logger.error(f"❌ Error loading config: {e}")
        
        return default_config
    
    def save_config(self, config_data):
        """Save configuration to JSON file"""
        try:
            # Update timestamps
            if not self.config['created_at']:
                self.config['created_at'] = datetime.now().isoformat()
            self.config['updated_at'] = datetime.now().isoformat()
            
            # Update config with new data
            for key, value in config_data.items():
                self.config[key] = value
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info("✅ Configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving config: {e}")
            return False
    
    def get_config(self):
        """Get current configuration"""
        return self.config
    
    def update_config(self, key, value):
        """Update single configuration value"""
        self.config[key] = value
        self.save_config(self.config)
    
    def validate_config(self):
        """Validate if configuration is complete"""
        required_fields = ['instagram_username', 'instagram_password', 
                          'telegram_token', 'admin_user_id']
        
        missing = []
        for field in required_fields:
            if not self.config.get(field):
                missing.append(field)
        
        return len(missing) == 0, missing