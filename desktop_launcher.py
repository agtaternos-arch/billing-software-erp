import os
import sys
import threading
import time
import socket
import webbrowser
import traceback
import urllib.request
import urllib.error

# Set settings to desktop version BEFORE any Django imports
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.desktop_settings'

APP_NAME = "Torvix Bills"

def get_free_port():
    """Find a free port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def get_lan_ip():
    """Get local LAN IP address."""
    lan_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('10.254.254.254', 1))
        lan_ip = s.getsockname()[0]
    except Exception:
        pass
    finally:
        s.close()
    return lan_ip

def run_django(port):
    """Start the Django server using Waitress on all interfaces for LAN access."""
    from waitress import serve
    from django.core.wsgi import get_wsgi_application
    
    application = get_wsgi_application()
    lan_ip = get_lan_ip()
    
    print(f"\n{'='*50}")
    print(f"  {APP_NAME} - Server Running")
    print(f"{'='*50}")
    print(f"  Local:   http://127.0.0.1:{port}")
    print(f"  Network: http://{lan_ip}:{port}")
    print(f"{'='*50}")
    print(f"\n  Other devices on WiFi can access this address.")
    print(f"  DO NOT close this window while using the app.\n")
    
    serve(application, host='0.0.0.0', port=port, threads=4)

def run_migrations():
    """Run Django migrations on startup."""
    import django
    django.setup()
    from django.core.management import call_command
    call_command('migrate', '--noinput')
    
    # Auto-create or force-reset default admin user for desktop installations
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@torvix.com'})
    admin_user.set_password('admin@123456')
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.save()
    
    # Ensure admin has owner profile
    from apps.accounts.models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=admin_user, defaults={'role': 'owner'})
    if profile.role != 'owner':
        profile.role = 'owner'
        profile.save()
    
    print("  [INFO] Guaranteed admin account access (username: admin / password: admin@123456)")

def wait_and_open_browser(url, port):
    """Wait for the server to be ready and capable of handling HTTP, then open the browser."""
    print("  Waiting for server to initialize (this might take 10-15 seconds)...", flush=True)
    
    max_retries = 40
    for i in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=1)
            break # HTTP success!
        except urllib.error.URLError as e:
            # If server responds with some HTTP error code (e.g. 400), it means Waitress is successfully up
            if hasattr(e, 'code'):
                break 
        except Exception:
            pass # Server not up yet, keep waiting...
            
        time.sleep(1)
    
    print("  Server is ready! Opening browser...", flush=True)
    try:
        if sys.platform.startswith('win'):
            # os.startfile is more reliable in PyInstaller than webbrowser.open
            os.startfile(url)
        else:
            webbrowser.open(url)
    except Exception as e:
        print(f"  Could not open browser automatically: {e}", flush=True)

def main():
    print(f"\n  Starting {APP_NAME}...\n")
    
    # 1. Run migrations
    try:
        print("  Running database migrations...")
        run_migrations()
        print("  Migrations complete.")
    except SystemExit:
        print("  Migrations finished (with system exit - this is normal).")
    except Exception as e:
        print(f"  Migration warning: {e}")
        traceback.print_exc()

    # 2. Find a port
    port = get_free_port()
    url = f"http://127.0.0.1:{port}"

    # 3. Start the browser launcher in a background thread
    launcher_thread = threading.Thread(target=wait_and_open_browser, args=(url, port), daemon=True)
    launcher_thread.start()

    # 4. Start Django in the main thread (this blocks indefinitely)
    print("\n  Press Ctrl+C to stop the server.\n")
    try:
        run_django(port)
    except KeyboardInterrupt:
        print(f"\n  Shutting down {APP_NAME}...")
    except BaseException as e:
        print(f"\n  Server stopped unexpectedly: {e}")
        traceback.print_exc()
        
    print("\n  Server has stopped running.")

if __name__ == '__main__':
    # Fix for multiprocessing in PyInstaller
    if sys.platform.startswith('win'):
        import multiprocessing
        multiprocessing.freeze_support()
    
    try:
        main()
    except BaseException as e:
        if isinstance(e, SystemExit) and e.code == 0:
            pass
        else:
            print(f"\n  FATAL ERROR: {e}")
            traceback.print_exc()
            
    input("\n  Press Enter to exit...")

