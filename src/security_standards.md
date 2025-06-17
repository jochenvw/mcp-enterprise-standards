### Required Security Standards

1. **Private Endpoints**
   Ensure that Azure PaaS/SaaS resources (e.g., Azure Storage, Key Vault, App Service) use **Private Endpoints**. Public access must be disabled where supported (`publicNetworkAccess: 'Disabled'` or equivalent).

2. **Network Security Groups (NSGs)**
   All subnets must be associated with an NSG. NSG rules should follow **least privilege**—deny by default and only allow explicitly required traffic.

3. **Azure AD Authentication & Managed Identity**
   Resources must enable **Azure Active Directory authentication** where applicable. **Managed identities** (system or user-assigned) must be used instead of client secrets or service principals.

4. **Secrets Management via Key Vault**
   Application secrets, connection strings, and certificates must be stored in **Azure Key Vault** and referenced via Key Vault bindings—not hardcoded.

5. **TLS & HTTPS Enforcement**
   All exposed endpoints must **enforce HTTPS-only** traffic and use **TLS 1.2 or higher**.

6. **Encryption at Rest**
   Resources must ensure **encryption at rest** is enabled. Where supported, **customer-managed keys (CMKs)** should be used when required by policy.

7. **Web Front Door / WAF / DDoS**
   Internet-facing workloads must be fronted by **Application Gateway with WAF** or **Azure Front Door**, and **DDoS Protection Standard** must be enabled on the relevant virtual networks.

8. **Security Monitoring**
   Defender for Cloud must be enabled and configured to monitor the resource types deployed. Built-in Azure Security Benchmark policies must be enforced.
