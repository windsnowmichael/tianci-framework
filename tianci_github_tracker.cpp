#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <sstream>
#include <cstdlib>
#include <algorithm>

#ifdef _WIN32
#include <windows.h>
#include <winhttp.h>
#pragma comment(lib, "winhttp.lib")
#endif

// 用 WinHTTP 请求 DNS over HTTPS，返回解析出的首个 IPv4
std::string resolve_domain_via_doh(const std::string& domain) {
    std::string response;
    HINTERNET hSession = WinHttpOpen(L"TianCi/1.0",
                                     WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                     WINHTTP_NO_PROXY_NAME,
                                     WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) return "";

    HINTERNET hConnect = WinHttpConnect(hSession, L"dns.alidns.com",
                                        INTERNET_DEFAULT_HTTPS_PORT, 0);
    if (!hConnect) { WinHttpCloseHandle(hSession); return ""; }

    std::string path_str = "/resolve?name=" + domain + "&type=A";
    std::wstring wpath(path_str.begin(), path_str.end());
    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"GET", wpath.c_str(),
                                            NULL, WINHTTP_NO_REFERER,
                                            WINHTTP_DEFAULT_ACCEPT_TYPES,
                                            WINHTTP_FLAG_SECURE);
    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return "";
    }

    if (!WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                           WINHTTP_NO_REQUEST_DATA, 0, 0, 0) ||
        !WinHttpReceiveResponse(hRequest, NULL)) {
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return "";
    }

    DWORD dwSize = 0, dwDownloaded = 0;
    char szBuffer[4096];
    do {
        dwSize = 0;
        if (!WinHttpQueryDataAvailable(hRequest, &dwSize)) break;
        if (dwSize == 0) break;
        if (dwSize > sizeof(szBuffer)) dwSize = sizeof(szBuffer);
        if (!WinHttpReadData(hRequest, szBuffer, dwSize, &dwDownloaded)) break;
        response.append(szBuffer, dwDownloaded);
    } while (dwSize > 0);

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);

    // 精确提取 A 记录的 IP
    size_t pos = 0;
    while (pos < response.length()) {
        size_t type_pos = response.find("\"type\":1", pos);
        if (type_pos == std::string::npos) break;
        size_t data_pos = response.find("\"data\":\"", type_pos);
        if (data_pos == std::string::npos) break;
        data_pos += 8;
        size_t data_end = response.find("\"", data_pos);
        if (data_end == std::string::npos) break;
        std::string ip = response.substr(data_pos, data_end - data_pos);
        if (ip.find('.') != std::string::npos && ip.length() <= 15) {
            return ip;
        }
        pos = data_end + 1;
    }
    return "";
}

// 已知 IP 兜底
std::map<std::string, std::vector<std::string>> KNOWN_IPS = {
    {"github.com", {"20.205.243.166", "140.82.121.3", "140.82.121.4"}},
    {"api.github.com", {"20.205.243.168", "140.82.116.5"}},
    {"github.global.ssl.fastly.net", {"157.240.16.50", "199.232.69.194"}},
    {"assets-cdn.github.com", {"185.199.110.133", "185.199.109.133"}},
    {"raw.githubusercontent.com", {"185.199.110.133", "185.199.108.133"}}
};

std::vector<std::string> GITHUB_DOMAINS = {
    "github.com", "api.github.com", "github.global.ssl.fastly.net",
    "assets-cdn.github.com", "raw.githubusercontent.com"
};

std::string HOSTS_PATH = "C:\\Windows\\System32\\drivers\\etc\\hosts";
const std::string HOSTS_START = "# GitHub TianCi Anchor Start";
const std::string HOSTS_END   = "# GitHub TianCi Anchor End";

std::string read_hosts() {
    std::ifstream file(HOSTS_PATH);
    if (!file.is_open()) return "";
    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

bool write_hosts(const std::string& content) {
    std::ofstream file(HOSTS_PATH, std::ios::out | std::ios::trunc);
    if (!file.is_open()) return false;
    file << content;
    return true;
}

void flush_dns() {
    system("ipconfig /flushdns > nul 2>&1");
}

bool is_admin() {
    HANDLE hToken;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken)) return false;
    TOKEN_ELEVATION elevation;
    DWORD dwSize;
    bool isElevated = false;
    if (GetTokenInformation(hToken, TokenElevation, &elevation, sizeof(elevation), &dwSize)) {
        isElevated = (elevation.TokenIsElevated != 0);
    }
    CloseHandle(hToken);
    return isElevated;
}

bool update_hosts(const std::map<std::string, std::string>& entries) {
    std::string content = read_hosts();
    std::string::size_type start_pos = content.find(HOSTS_START);
    while (start_pos != std::string::npos) {
        std::string::size_type end_pos = content.find(HOSTS_END, start_pos);
        if (end_pos == std::string::npos) break;
        content.erase(start_pos, end_pos - start_pos + HOSTS_END.length());
        start_pos = content.find(HOSTS_START, start_pos);
    }

    std::string new_block = "\n" + HOSTS_START + "\n";
    for (const auto& entry : entries) new_block += entry.second + " " + entry.first + "\n";
    new_block += HOSTS_END + "\n";

    std::string final_content = content + new_block;
    if (!write_hosts(final_content)) {
        std::cerr << "写入 hosts 失败，请检查权限。" << std::endl;
        return false;
    }
    flush_dns();
    std::cout << "✅ hosts 已更新，DNS 缓存已刷新。" << std::endl;
    return true;
}

int main() {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
#endif
    std::cout << "🌍 天赐范式 · GitHub DNS 加速器 (C++ WinHTTP 版)" << std::endl;

    if (!is_admin()) {
        std::cerr << "❌ 请以管理员身份运行此程序！" << std::endl;
        return 1;
    }

    std::map<std::string, std::string> ip_map;
    for (const auto& domain : GITHUB_DOMAINS) {
        std::cout << "正在解析 " << domain << " ... ";
        std::string ip = resolve_domain_via_doh(domain);
        if (!ip.empty()) {
            std::cout << "✅ " << ip << std::endl;
            ip_map[domain] = ip;
        } else if (KNOWN_IPS.find(domain) != KNOWN_IPS.end() && !KNOWN_IPS[domain].empty()) {
            ip = KNOWN_IPS[domain][0];
            std::cout << "⚠️ DoH失败，使用已知IP: " << ip << std::endl;
            ip_map[domain] = ip;
        } else {
            std::cout << "❌ 无可用IP" << std::endl;
        }
    }

    if (ip_map.empty()) {
        std::cerr << "❌ 没有获取到任何有效 IP。" << std::endl;
        return 1;
    }

    if (update_hosts(ip_map)) std::cout << "✅ 加速器已生效！" << std::endl;
    return 0;
}