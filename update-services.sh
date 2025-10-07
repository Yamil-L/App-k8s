for service in translation summary analytics improve keywords; do
    cd /mnt/d/U/cloud/parcial/repo-root/microservices/$service
    
    # Actualizar main.py para intentar diferentes modelos
    sed -i "s/model = genai.GenerativeModel('gemini-1.5-flash')/try:\n    model = genai.GenerativeModel('gemini-2.5-flash')\nexcept:\n    model = genai.GenerativeModel('gemini-pro-latest')/" main.py
    
    docker build -t text-processor-$service:v4 .
    k3d image import text-processor-$service:v4 -c mycluster
done
