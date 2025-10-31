Name:           wapiti-arsenic
Version:        28.5
Release:        1%{?dist}
Summary:        Asynchronous WebDriver client used by Wapiti web scanner
License:        Apache-2.0
URL:            https://github.com/wapiti-scanner/arsenic
Source0:        %{name}-%{version}.tar.gz
Source1:        wapiti_arsenic-%{version}-py3-none-any.whl
BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-pip
Requires:       python3, python3-httpx >= 0.27, python3-packaging >=23.0

%description
Wapiti-Arsenic provides an asyncio-compatible WebDriver API wrapper
for headless browser automation used in the Wapiti web vulnerability scanner.

%prep
# Pas besoin d'extraire le tarball, on utilise directement le wheel

%build
# Le wheel est déjà construit par Poetry

%install
%{__python3} -m pip install --no-deps --root %{buildroot} --ignore-installed %{SOURCE1}

%files
%license %{python3_sitelib}/LICENSE
%doc %{python3_sitelib}/README.md
%{_bindir}/arsenic-check-ie11
%{_bindir}/arsenic-configure-ie11
%{python3_sitelib}/wapiti_arsenic*

%changelog
* Mon Oct 06 2025 Nicolas Surribas <nicolas.surribas@gmail.com> - 28.4
- Initial RPM packaging