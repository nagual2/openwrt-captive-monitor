import paramiko
import os
import sys

def test_ssh_connection(hostname, username, key_path=None, password=None):
    print(f"Попытка подключения к {username}@{hostname}...")
    
    try:
        # Создаем SSH-клиент
        ssh = paramiko.SSHClient()
        
        # Загружаем known_hosts для верификации ключа хоста
        ssh.load_system_host_keys()
        # nosec B507 - For local testing only. Uses WarningPolicy instead of AutoAddPolicy
        # to warn about unknown host keys while still allowing connections for development
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        
        # Параметры подключения
        kwargs = {
            'hostname': hostname,
            'username': username,
            'timeout': 10
        }
        
        # Используем ключ, если он указан, иначе запрашиваем пароль
        if key_path and os.path.exists(key_path):
            print(f"Используем ключ: {key_path}")
            private_key = paramiko.RSAKey.from_private_key_file(key_path)
            kwargs['pkey'] = private_key
        elif password is None:
            import getpass
            password = getpass.getpass("Введите пароль: ")
            kwargs['password'] = password
        else:
            kwargs['password'] = password
        
        # Подключаемся
        ssh.connect(**kwargs)
        print("✓ Подключение установлено!")
        
        # Выполняем команду
        stdin, stdout, stderr = ssh.exec_command('uname -a && echo "Тест русского языка"')
        
        # Выводим результат
        print("\nРезультат выполнения команды:")
        print(stdout.read().decode().strip())
        
        # Закрываем соединение
        ssh.close()
        print("\n✓ Соединение закрыто")
        
    except Exception as e:
        print(f"\nОшибка: {str(e)}")
        if "Authentication" in str(e):
            print("Ошибка аутентификации. Проверьте учетные данные или ключ доступа.")
        elif "No such file or directory" in str(e):
            print("Файл ключа не найден. Проверьте путь к ключу.")
        elif "timed out" in str(e).lower():
            print("Таймаут подключения. Проверьте доступность хоста и сеть.")

if __name__ == "__main__":
    # Параметры подключения (используйте переменные окружения)
    import os
    HOST = os.getenv("SSH_HOST", "192.168.1.1")
    USER = os.getenv("SSH_USER", "root")
    
    # Пути к ключам (используйте переменные окружения или пути по умолчанию)
    default_key_paths = [
        os.path.expanduser("~/.ssh/id_rsa"),
        os.path.expanduser("~/.ssh/id_ed25519"),
        os.path.expanduser("~/.ssh/id_ecdsa")
    ]
    
    # Дополнительные пути из переменных окружения
    custom_key_path = os.getenv("SSH_KEY_PATH")
    if custom_key_path:
        default_key_paths.insert(0, custom_key_path)
    
    print("Проверка доступных ключей...")
    available_keys = [k for k in default_key_paths if os.path.exists(k)]
    
    if available_keys:
        print(f"Найдены ключи: {', '.join(available_keys)}")
        for key in available_keys:
            print(f"\nПопытка подключения с ключом: {key}")
            test_ssh_connection(HOST, USER, key_path=key)
    else:
        print("Ключи не найдены, пробуем подключение по паролю...")
        test_ssh_connection(HOST, USER)
