import ipaddress
import pandas as pd

# 云防节点IP段
cloud_defense_ip_ranges = [
   # 自己填入WAF节点IP
]

# 客户内部IP段
customer_internal_ip_ranges = [
   # 自己填入客户内部IP
]


# 将特定格式的IP段转换为ip_network可识别的列表
def expand_ip_range(ip_range):
    if "-" in ip_range:
        start, end = ip_range.split("-")
        start_base = ".".join(start.split(".")[:3])
        start_last_part = int(start.split(".")[-1])
        end_last_part = int(end)
        return [
            ipaddress.ip_network(f"{start_base}.{i}/32")
            for i in range(start_last_part, end_last_part + 1)
        ]
    else:
        return [ipaddress.ip_network(ip_range)]


cloud_defense_nets = []
for ip_range in cloud_defense_ip_ranges:
    cloud_defense_nets.extend(expand_ip_range(ip_range))

customer_internal_nets = []
for ip_range in customer_internal_ip_ranges:
    customer_internal_nets.extend(expand_ip_range(ip_range))


# 定义函数检查IP类型（内网IP或互联网IP）
def check_ip_type(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private:
            return "内网ip"
        else:
            return "互联网ip"
    except ValueError:
        return "无效ip"


# 检查IP是否为云防节点IP
def is_cloud_defense_ip(ip, cloud_defense_nets):
    ip_obj = ipaddress.ip_address(ip)
    for ip_net in cloud_defense_nets:
        if ip_obj in ip_net:
            return "云防节点IP段"
    return "否"


# 检查IP是否为客户IP
def is_customer_ip(ip, customer_ip_nets):
    ip_obj = ipaddress.ip_address(ip)
    for ip_net in customer_ip_nets:
        if ip_obj in ip_net:
            return "客户内部IP段"
    return "否"


# 检查IP是否被封禁（不是客户IP段且不是云防节点IP段且不是内网IP即为被封禁）
def check_if_banned(is_customer, is_cloud_defense, ip_type):
    return (
        "否"
        if is_customer == "客户内部IP段"
        or is_cloud_defense == "云防节点IP段"
        or ip_type == "内网ip"
        else "是"
    )


# 从文件中读取IP地址列表
with open("ip.txt", "r") as file:
    ips_to_check = file.read().splitlines()

# 过滤掉非法的IP地址
valid_ips = []
for ip in ips_to_check:
    try:
        ipaddress.ip_address(ip)
        valid_ips.append(ip)
    except ValueError:
        print(f"Invalid IP address: {ip}")

# 创建一个DataFrame来存储结果
df = pd.DataFrame(columns=["ip", "ip类型", "是否为客户ip", "是否为封禁ip"])

# 分析每个IP地址
for ip in valid_ips:
    ip_type = check_ip_type(ip)
    cloud_defense_ip = is_cloud_defense_ip(ip, cloud_defense_nets)
    customer_ip = is_customer_ip(ip, customer_internal_nets)
    is_banned = check_if_banned(customer_ip, cloud_defense_ip, ip_type)
    new_row = pd.DataFrame(
        [
            {
                "ip": ip,
                "ip类型": ip_type,
                "是否为客户ip": (
                    customer_ip if customer_ip == "客户内部IP段" else cloud_defense_ip
                ),
                "是否为封禁ip": is_banned,
            }
        ]
    )
    df = pd.concat([df, new_row], ignore_index=True)

# 输出到Excel文件
df.to_excel("filtered_ips-1.xlsx", index=False)
