#!/usr/bin/env python3
"""
Патч для добавления cleanup дочерних процессов в captive_portal_selenium.py
"""

import sys

# Читаем файл
with open('/usr/local/bin/captive_portal_selenium.py', 'r') as f:
    content = f.read()

# Новый finally блок с cleanup
new_finally = '''        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                
                # Принудительная очистка дочерних процессов
                try:
                    import subprocess
                    import signal
                    
                    # Убиваем все chromedriver процессы текущего пользователя
                    subprocess.run(['pkill', '-9', '-f', 'chromedriver'], 
                                   stderr=subprocess.DEVNULL, check=False)
                    
                    # Убиваем все headless chrome процессы текущего пользователя
                    subprocess.run(['pkill', '-9', '-f', 'google-chrome.*headless'], 
                                   stderr=subprocess.DEVNULL, check=False)
                except:
                    pass'''

# Заменяем старый finally блок
old_finally = '''        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass'''

if old_finally in content:
    content = content.replace(old_finally, new_finally)
    
    # Записываем обратно
    with open('/usr/local/bin/captive_portal_selenium.py', 'w') as f:
        f.write(content)
    
    print("✅ Патч применён успешно")
    sys.exit(0)
else:
    print("❌ Не найден блок для замены")
    sys.exit(1)
