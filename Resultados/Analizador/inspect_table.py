from supabase import create_client, Client

SUPABASE_URL = "https://fnpcclnzbdrzzbcoeqhm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZucGNjbG56YmRyenpiY29lcWhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyNzAyNDUsImV4cCI6MjA3Mjg0NjI0NX0.0qzERgm-Nf_wiHMuijnf7X2vMX0k3oz4wyszKoo2sN0"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Consultando tabla Hallazgo...")
    response = supabase.table('Hallazgo').select("*").limit(1).execute()
    print("Datos:", response.data)
    if response.data:
        print("Columnas:", response.data[0].keys())
    else:
        print("La tabla está vacía, no puedo inferir columnas.")
except Exception as e:
    print(f"Error: {e}")
