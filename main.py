# main.py
import flet as ft
import logging
import httpx
import json
from datetime import datetime
from components.chat_panel import ChatPanel
from components.memory_list_panel import MemoryListPanel
from components.trainer_panel import TrainerPanel
from components.cleanup_panel import CleanupPanel
from components.settings_panel import SettingsPanel
from components.intent_analytics_panel import IntentAnalyticsPanel
from components.ai_intent_group_panel import AIIntentGroupPanel
from components.export_panel import ExportPanel
from components.login_panel import LoginPanel
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env dosyasını yükle
load_dotenv()

# FastAPI uygulaması oluştur
app = FastAPI()

# Statik dosyalar için mount
app.mount("/static", StaticFiles(directory="static"), name="static")

class CloudLLMApp:
    def __init__(self):
        # .env dosyasını yükle
        load_dotenv()
        
        # Supabase URL ve API key'i kontrol et
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logging.error("SUPABASE_URL veya SUPABASE_KEY bulunamadı!")
            raise ValueError("Lütfen .env dosyasında SUPABASE_URL ve SUPABASE_KEY değerlerini tanımlayın.")
            
        try:
            # API key'i temizle
            self.supabase_key = self.supabase_key.strip()
            if self.supabase_key.endswith('%'):
                self.supabase_key = self.supabase_key[:-1]
                
            logging.info(f"Supabase URL: {self.supabase_url}")
            logging.info(f"Supabase Key: {self.supabase_key[:20]}...")
                
            # Supabase istemcisini oluştur
            self.supabase: Client = create_client(
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key
            )
            self.supabase_manager = self.supabase
            logging.info("Supabase istemcisi oluşturuldu")
            
            # Bağlantıyı test et
            self.test_supabase_connection()
            
        except Exception as e:
            logging.error(f"Supabase bağlantı hatası: {str(e)}")
            raise ConnectionError(f"Supabase bağlantısı kurulamadı: {str(e)}")
            
        self.token = None
        self.user_id = None
        self.language = "tr"
        self.tts_enabled = True
        self.stt_enabled = True
        self.page = None
        
        # Tema ayarları
        self.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=ft.Colors.BLUE,
                on_primary=ft.Colors.WHITE,
                primary_container=ft.Colors.BLUE_100,
                on_primary_container=ft.Colors.BLUE_900,
                secondary=ft.Colors.BLUE_400,
                on_secondary=ft.Colors.WHITE,
                error=ft.Colors.RED_600,
                on_error=ft.Colors.WHITE,
                background=ft.Colors.WHITE,
                on_background=ft.Colors.BLACK,
                surface=ft.Colors.WHITE,
                on_surface=ft.Colors.BLACK,
            ),
            use_material3=True
        )

    def test_supabase_connection(self):
        """Supabase bağlantısını test et"""
        try:
            # Basit bir sorgu dene
            response = self.supabase.table('profiles').select("count").execute()
            logging.info("Supabase bağlantı testi başarılı!")
            return True
        except Exception as e:
            logging.error(f"Supabase bağlantı testi başarısız: {str(e)}")
            raise ConnectionError(f"Supabase bağlantı testi başarısız: {str(e)}")

    async def _handle_did_mount(self, control):
        """Kontrolün ve alt kontrollerinin did_mount metodlarını çağır"""
        try:
            # Önce alt kontrolleri işle
            if hasattr(control, "content") and control.content:
                await self._handle_did_mount(control.content)

            if hasattr(control, "controls"):
                for child in control.controls:
                    if child:
                        await self._handle_did_mount(child)

            if isinstance(control, ft.Tabs) and control.tabs:
                for tab in control.tabs:
                    if tab and tab.content:
                        await self._handle_did_mount(tab.content)

            # En son did_mount'u çağır
            if hasattr(control, "did_mount") and callable(control.did_mount):
                if asyncio.iscoroutinefunction(control.did_mount):
                    await control.did_mount()
                else:
                    control.did_mount()

        except Exception as e:
            logger.error(f"Kontrol eklenirken hata: {str(e)}")
            raise
        
    async def login(self, email: str, password: str):
        """Supabase'e giriş yap ve token al"""
        try:
            # E-posta ve şifreyi temizle
            email = email.strip()
            password = password.strip()
            
            logging.info(f"Giriş denemesi: {email}")
            
            # Giriş yap
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            logging.info(f"Auth yanıtı: {auth_response}")
            
            if auth_response and hasattr(auth_response.user, 'id'):
                self.token = auth_response.session.access_token
                self.user_id = auth_response.user.id
                
                # Kullanıcı profilini al
                profile = self.supabase.from_('profiles').select('*').eq('id', self.user_id).single().execute()
                
                if profile and profile.data:
                    logging.info(f"Profil bilgisi: {profile.data}")
                    self.show_success(f"Hoş geldiniz, {profile.data.get('full_name', '')}!")
                else:
                    self.show_success("Başarıyla giriş yapıldı!")
                    
                return True
                
            self.show_error("Giriş başarısız. E-posta veya şifre hatalı.")
            return False
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Giriş hatası detayı: {error_msg}")
            
            if "Invalid API key" in error_msg:
                logging.error(f"Supabase API key: {self.supabase_key}")
                self.show_error("Supabase API anahtarı geçersiz. Lütfen sistem yöneticisi ile iletişime geçin.")
            elif "Invalid login credentials" in error_msg:
                self.show_error("Giriş bilgileri geçersiz. Lütfen e-posta ve şifrenizi kontrol edin.")
            elif "Email not confirmed" in error_msg:
                self.show_error("E-posta adresiniz henüz doğrulanmamış. Lütfen e-postanızı kontrol edin.")
            else:
                self.show_error(f"Giriş yapılırken bir hata oluştu: {error_msg}")
            return False
            
    async def register(self, email: str, password: str, full_name: str):
        """Yeni kullanıcı kaydı"""
        try:
            # Verileri temizle
            email = email.strip()
            password = password.strip()
            full_name = full_name.strip()
            
            logging.info(f"Kayıt denemesi: {email}")
            
            # Kayıt ol
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            logging.info(f"Kayıt yanıtı: {auth_response}")
            
            if auth_response and hasattr(auth_response.user, 'id'):
                self.show_success("Kayıt başarılı! Lütfen e-posta adresinizi doğrulayın.")
                return True
                
            self.show_error("Kayıt başarısız.")
            return False
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Kayıt hatası detayı: {error_msg}")
            
            if "User already registered" in error_msg:
                self.show_error("Bu e-posta adresi zaten kayıtlı.")
            else:
                self.show_error(f"Kayıt olurken bir hata oluştu: {error_msg}")
            return False
            
    async def main(self, page: ft.Page):
        self.page = page
        page.title = "Cloud AI"
        page.theme = self.theme
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.spacing = 20
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 800
        page.window_min_height = 600
        
        # AppBar oluştur
        page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.CLOUD_QUEUE, size=32, color=ft.Colors.WHITE),
            leading_width=40,
            title=ft.Text("Cloud AI", size=28, weight="bold", color=ft.Colors.WHITE),
            center_title=False,
            bgcolor=ft.Colors.PRIMARY,
            actions=[
                ft.Container(
                    content=ft.Row(
                        [
                            ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(
                                        text="Sohbet",
                                        icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                                        on_click=lambda _: self.switch_tab(0)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Hafıza",
                                        icon=ft.Icons.MEMORY,
                                        on_click=lambda _: self.switch_tab(1)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Eğitici",
                                        icon=ft.Icons.SCHOOL_OUTLINED,
                                        on_click=lambda _: self.switch_tab(2)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Temizle",
                                        icon=ft.Icons.CLEANING_SERVICES_OUTLINED,
                                        on_click=lambda _: self.switch_tab(3)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Ayarlar",
                                        icon=ft.Icons.SETTINGS_OUTLINED,
                                        on_click=lambda _: self.switch_tab(4)
                                    ),
                                    ft.PopupMenuItem(
                                        text="İstatistikler",
                                        icon=ft.Icons.ANALYTICS_OUTLINED,
                                        on_click=lambda _: self.switch_tab(5)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Intent Grupları",
                                        icon=ft.Icons.GROUP_WORK_OUTLINED,
                                        on_click=lambda _: self.switch_tab(6)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Önemli Öğrenmeler",
                                        icon=ft.Icons.STAR_OUTLINE,
                                        on_click=lambda _: self.switch_tab(7)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Dışa Aktar",
                                        icon=ft.Icons.UPLOAD_FILE,
                                        on_click=lambda _: self.switch_tab(8)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Eşleşme Geçmişi",
                                        icon=ft.Icons.HISTORY,
                                        on_click=lambda _: self.switch_tab(9)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Intent Birleştir",
                                        icon=ft.Icons.MERGE,
                                        on_click=lambda _: self.switch_tab(10)
                                    ),
                                    ft.PopupMenuItem(
                                        text="Toplu Silme",
                                        icon=ft.Icons.DELETE_SWEEP,
                                        on_click=lambda _: self.switch_tab(11)
                                    ),
                                ],
                                icon=ft.Icons.MENU,
                                icon_color=ft.Colors.WHITE
                            ),
                            ft.Icon(ft.Icons.VOLUME_UP, color=ft.Colors.WHITE),
                            ft.Text("TTS", color=ft.Colors.WHITE),
                            ft.Switch(
                                label="",
                                value=True,
                                active_color=ft.Colors.WHITE,
                                active_track_color=ft.Colors.WHITE24,
                                inactive_thumb_color=ft.Colors.WHITE70,
                                inactive_track_color=ft.Colors.WHITE24,
                                on_change=lambda e: self.toggle_tts(e)
                            ),
                            ft.Icon(ft.Icons.DARK_MODE, color=ft.Colors.WHITE),
                            ft.Text("Karanlık Mod", color=ft.Colors.WHITE),
                            ft.Switch(
                                label="",
                                value=False,
                                active_color=ft.Colors.WHITE,
                                active_track_color=ft.Colors.WHITE24,
                                inactive_thumb_color=ft.Colors.WHITE70,
                                inactive_track_color=ft.Colors.WHITE24,
                                on_change=lambda e: self.toggle_theme(e)
                            ),
                            ft.ElevatedButton(
                                text="Giriş Yap" if not self.token else "Çıkış Yap",
                                icon=ft.Icons.LOGIN if not self.token else ft.Icons.LOGOUT,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.PRIMARY,
                                    bgcolor=ft.Colors.WHITE
                                ),
                                on_click=self.toggle_auth
                            )
                        ],
                        spacing=10
                    ),
                    padding=10
                )
            ]
        )
        
        # Panelleri oluştur
        self.panels = [
            ChatPanel(self),
            MemoryListPanel(self),
            TrainerPanel(self),
            CleanupPanel(self),
            SettingsPanel(self),
            IntentAnalyticsPanel(self),
            AIIntentGroupPanel(self),
            ExportPanel(self),
        ]

        # Panelleri sayfaya ekle
        for panel in self.panels:
            page.add(
                ft.Container(
                    content=panel,
        padding=20,
                    expand=True,
                    visible=False
                )
            )

        # İlk paneli görünür yap
        page.controls[0].visible = True

        # did_mount çağrılarını yap
        for panel in self.panels:
            if hasattr(panel, "did_mount") and callable(panel.did_mount):
                if asyncio.iscoroutinefunction(panel.did_mount):
                    await panel.did_mount()
                else:
                    panel.did_mount()

        # Sayfayı güncelle
        await page.update_async()

    def toggle_tts(self, e):
        """TTS'yi aç/kapat"""
        self.tts_enabled = e.control.value
        self.show_success(f"TTS {'açıldı' if e.control.value else 'kapandı'}")
        
    def toggle_theme(self, e):
        """Tema modunu değiştir"""
        if e.control.value:
            # Karanlık mod
            self.page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=ft.Colors.BLUE,
                    on_primary=ft.Colors.WHITE,
                    primary_container=ft.Colors.BLUE_900,
                    on_primary_container=ft.Colors.BLUE_100,
                    secondary=ft.Colors.BLUE_200,
                    on_secondary=ft.Colors.BLACK,
                    error=ft.Colors.RED_200,
                    on_error=ft.Colors.BLACK,
                    background=ft.Colors.GREY_900,
                    on_background=ft.Colors.WHITE,
                    surface=ft.Colors.GREY_800,
                    on_surface=ft.Colors.WHITE,
                    surface_tint=ft.Colors.BLUE_700,
                    outline=ft.Colors.GREY_600,
                ),
                use_material3=True
            )
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            # Aydınlık mod
            self.page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=ft.Colors.BLUE,
                    on_primary=ft.Colors.WHITE,
                    primary_container=ft.Colors.BLUE_100,
                    on_primary_container=ft.Colors.BLUE_900,
                    secondary=ft.Colors.BLUE_600,
                    on_secondary=ft.Colors.WHITE,
                    error=ft.Colors.RED_600,
                    on_error=ft.Colors.WHITE,
                    background=ft.Colors.WHITE,
                    on_background=ft.Colors.BLACK,
                    surface=ft.Colors.WHITE,
                    on_surface=ft.Colors.BLACK,
                    surface_tint=ft.Colors.BLUE_100,
                    outline=ft.Colors.GREY_400,
                ),
                use_material3=True
            )
            self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.update()
        
    def show_error(self, message):
        """Hata mesajı göster"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.RED),
            bgcolor=ft.Colors.ERROR,
            show_close_icon=True,
            close_icon_color=ft.Colors.WHITE
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    def show_success(self, message):
        """Başarı mesajı göster"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.GREEN),
            bgcolor=ft.Colors.SURFACE_TINT,
            show_close_icon=True,
            close_icon_color=ft.Colors.WHITE
        )
        self.page.snack_bar.open = True
        self.page.update()

    async def get_response(self, message):
        """Kullanıcı mesajına yanıt ver"""
        try:
            if not self.token or not self.user_id:
                return "Lütfen önce giriş yapın."

            # Supabase'den en uygun yanıtı bul
            response = self.supabase.table("memories").select("*").execute()
            
            if not response.data:
                return "Henüz hafızamda kayıtlı yanıt yok."
                
            # En basit eşleştirme: Aynı prompt'u ara
            for memory in response.data:
                if message.lower() in memory["prompt"].lower():
                    # Kullanım sayısını artır
                    self.supabase.table("memories").update(
                        {"usage_count": memory["usage_count"] + 1}
                    ).eq("id", memory["id"]).execute()
                    
                    return memory["response"]
                    
            return "Bu konuda henüz bir bilgim yok."
            
        except Exception as e:
            logging.error(f"Yanıt alma hatası: {str(e)}")
            return "Bağlantı hatası. Lütfen internet bağlantınızı kontrol edin."

    def switch_tab(self, index):
        """Sekme değiştir"""
        if 0 <= index < len(self.page.controls):
            # Tüm panelleri gizle
            for control in self.page.controls:
                control.visible = False

            # Seçilen paneli göster
            self.page.controls[index].visible = True
            self.page.update()

    async def toggle_auth(self, e):
        """Giriş/çıkış işlemlerini yönet"""
        if not self.token:
            # Giriş yapma sayfasına yönlendir
            self.page.clean()
            self.page.add(LoginPanel(self))
        else:
            # Çıkış yap
            try:
                await self.supabase.auth.sign_out()
                self.token = None
                self.user_id = None
                self.show_success("Başarıyla çıkış yapıldı")
                self.page.clean()
                await self.main(self.page)
            except Exception as e:
                self.show_error(f"Çıkış yapılırken hata: {str(e)}")

# FastAPI endpoint'leri
@app.get("/")
async def root():
    return {"message": "Cloud AI API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Flet uygulamasını başlat
    flet_app = CloudLLMApp()
    ft.app(
        target=flet_app.main,
        view=ft.AppView.FLET_APP,
        assets_dir="static",
        name="Cloud AI"
    )
    
    # FastAPI uygulamasını başlat
    uvicorn.run(app, host="0.0.0.0", port=8000)
