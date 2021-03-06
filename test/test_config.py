import os

ngx_dir = "nginx"
download_dir = os.path.join(ngx_dir, "download")
conf_file = "nginx.conf"

links = {
"nginx_upstream_check_module": "https://codeload.github.com/Refinitiv/nginx_upstream_check_module/tar.gz/master#nginx_upstream_check_module-master",
"pcre" : "https://ftp.pcre.org/pub/pcre/pcre-8.41.tar.gz",
"zlib" : "https://zlib.net/zlib-1.2.11.tar.gz",
"openssl": "https://www.openssl.org/source/openssl-1.0.2k.tar.gz",
"nginx": "https://nginx.org/download/nginx-1.12.0.tar.gz"
}

ws_backend = "http://brokerstats-test.financial.com/streaming"
ws_backend = "http://127.0.0.1:5000/streaming"
ws_log_file = "logs/websocket.log"
proxy_port = 8080
workers = 1

conf_template = """
events
{{
   worker_connections 4096;
}}

worker_processes  {workers};

http
{{
   server
   {{
      ws_log {log};
      ws_log_format "$time_local: packet from $ws_packet_source, type: $ws_opcode, payload: $ws_payload_size";
      ws_log_format open "$time_local: Connection opened";
      ws_log_format close "$time_local: Connection closed";
#      ws_max_connections 1;
#      ws_conn_age 12h;
      listen {port};
      location /stat {{
         ws_stat;
      }}
      location /status {{
         stub_status;
      }}
      location /streaming {{
         proxy_pass {backend};
         proxy_set_header Upgrade $http_upgrade;
         proxy_set_header Connection "keep-alive, Upgrade";
         proxy_http_version 1.1;                           
         proxy_read_timeout 40s;
         proxy_send_timeout 12h;
      }}
   }}

}}
"""
