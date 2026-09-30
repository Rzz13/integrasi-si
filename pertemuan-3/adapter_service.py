from http.server import HTTPServer, BaseHTTPRequestHandler
import xml.etree.ElementTree as ET
import urllib.parse
import os

DB_FILE = "students_db.txt"

def read_db():
    students = []
    if not os.path.exists(DB_FILE):
        return students
    with open(DB_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) == 4:
                students.append({
                    "nim": parts[0],
                    "nama": parts[1],
                    "jurusan": parts[2],
                    "status": parts[3]
                })
    return students

def write_record(nim, nama, jurusan, status):
    with open(DB_FILE, "a") as f:
        f.write(f"{nim},{nama},{jurusan},{status}\n")

class EAIAdapterHandler(BaseHTTPRequestHandler):

    def _set_xml_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Endpoint: GET /students (Ambil semua data)
        if parsed_url.path == "/students":
            students = read_db()
            root = ET.Element("StudentDirectoryResponse")
            root.set("adapter_pattern", "EAI_Legacy_Wrapper")
            
            records_node = ET.SubElement(root, "Students")
            for s in students:
                student_node = ET.SubElement(records_node, "Student")
                ET.SubElement(student_node, "NIM").text = s["nim"]
                ET.SubElement(student_node, "Nama").text = s["nama"]
                ET.SubElement(student_node, "Jurusan").text = s["jurusan"]
                ET.SubElement(student_node, "Status").text = s["status"]

            xml_data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            self._set_xml_headers(200)
            self.wfile.write(xml_data)

        # Endpoint: GET /students/<nim> (Ambil data berdasarkan NIM)
        elif parsed_url.path.startswith("/students/"):
            target_nim = parsed_url.path.split("/")[-1]
            students = read_db()
            found = next((s for s in students if s["nim"] == target_nim), None)

            if found:
                root = ET.Element("StudentResponse")
                ET.SubElement(root, "NIM").text = found["nim"]
                ET.SubElement(root, "Nama").text = found["nama"]
                ET.SubElement(root, "Jurusan").text = found["jurusan"]
                ET.SubElement(root, "Status").text = found["status"]
                
                xml_data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                self._set_xml_headers(200)
                self.wfile.write(xml_data)
            else:
                root = ET.Element("ErrorResponse")
                ET.SubElement(root, "Code").text = "404"
                ET.SubElement(root, "Message").text = f"NIM {target_nim} tidak ditemukan pada berkas legacy"
                xml_data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                self._set_xml_headers(404)
                self.wfile.write(xml_data)
        else:
            self.send_error(404, "Endpoint tidak valid")

    def do_POST(self):
        # Endpoint: POST /students (Menerima input XML dari klien)
        if self.path == "/students":
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length)

            try:
                # Parsing XML dari request body
                xml_root = ET.fromstring(post_body)
                nim = xml_root.find("NIM").text
                nama = xml_root.find("Nama").text
                jurusan = xml_root.find("Jurusan").text
                status = xml_root.find("Status").text

                # Tulis data ke basis data legacy
                write_record(nim, nama, jurusan, status)

                # Format balasan XML
                root = ET.Element("OperationStatus")
                ET.SubElement(root, "Success").text = "true"
                ET.SubElement(root, "Message").text = f"Data mahasiswa {nim} berhasil disinkronisasi ke basis data legacy."
                xml_data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                
                self._set_xml_headers(201)
                self.wfile.write(xml_data)

            except Exception as e:
                root = ET.Element("OperationStatus")
                ET.SubElement(root, "Success").text = "false"
                ET.SubElement(root, "Error").text = str(e)
                xml_data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                self._set_xml_headers(400)
                self.wfile.write(xml_data)
        else:
            self.send_error(404, "Endpoint tidak valid")

if __name__ == "__main__":
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, EAIAdapterHandler)
    print("==================================================")
    print("EAI XML Adapter aktif di http://localhost:8000")
    print("Tekan Ctrl+C untuk menghentikan server.")
    print("==================================================")
    httpd.serve_forever()