import { useState, useEffect } from 'react';

export default function App() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeMenu, setActiveMenu] = useState('customers'); // Alapértelmezetten ide érkezünk
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');

  const [activeFormTab, setActiveFormTab] = useState('basic');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCompanyId, setEditingCompanyId] = useState(null);
  
  const [companyForm, setCompanyForm] = useState({
    company_name: '', brand_name: '', tax_number: '', eu_tax_number: '',
    industry: 'Textilipar', status: 'active', company_type: 'business', role_type: 'customer',
    billing_address: '', shipping_address: '', payment_terms: '8', currency: 'HUF',
    internal_notes: '', contacts: []
  });

  const fetchCompanies = () => {
    setLoading(true);
    fetch('http://127.0.0.1:8000/companies')
      .then((res) => res.json())
      .then((data) => { setCompanies(data); setLoading(false); })
      .catch((err) => { console.error(err); setLoading(false); });
  };

  useEffect(() => { fetchCompanies(); }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const url = editingCompanyId ? `http://127.0.0.1:8000/companies/${editingCompanyId}` : 'http://127.0.0.1:8000/companies';
    const method = editingCompanyId ? 'PUT' : 'POST';

    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(companyForm),
    })
      .then(() => { closeModal(); fetchCompanies(); })
      .catch((err) => console.error(err));
  };

  const addContactField = () => {
    setCompanyForm({ ...companyForm, contacts: [...companyForm.contacts, { name: '', email: '', phone: '', role: 'Beszerző' }] });
  };

  const handleContactChange = (index, field, value) => {
    const updatedContacts = [...companyForm.contacts];
    updatedContacts[index][field] = value;
    setCompanyForm({ ...companyForm, contacts: updatedContacts });
  };

  const removeContactField = (index) => {
    setCompanyForm({ ...companyForm, contacts: companyForm.contacts.filter((_, i) => i !== index) });
  };

  const openEditModal = (company) => {
    setEditingCompanyId(company.id);
    setCompanyForm({
      company_name: company.company_name, brand_name: company.brand_name || '',
      tax_number: company.tax_number || '', eu_tax_number: company.eu_tax_number || '',
      industry: company.industry || 'Textilipar', status: company.status || 'active',
      company_type: company.company_type || 'business', role_type: company.role_type || 'customer',
      billing_address: company.billing_address || '', shipping_address: company.shipping_address || '',
      payment_terms: company.payment_terms || '8', currency: company.currency || 'HUF',
      internal_notes: company.internal_notes || '', contacts: company.contacts || []
    });
    setActiveFormTab('basic');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingCompanyId(null);
    setActiveFormTab('basic');
    setCompanyForm({
      company_name: '', brand_name: '', tax_number: '', eu_tax_number: '',
      industry: 'Textilipar', status: 'active', company_type: 'business', role_type: 'customer',
      billing_address: '', shipping_address: '', payment_terms: '8', currency: 'HUF',
      internal_notes: '', contacts: []
    });
  };

  const handleDelete = (id) => {
    if (window.confirm("Biztosan törölni szeretnéd ezt a partnert a rendszerből?")) {
      fetch(`http://127.0.0.1:8000/companies/${id}`, { method: 'DELETE' }).then(() => fetchCompanies());
    }
  };

  // Szuper-kereső: Név, brand, adószám, iparág alapján is keres egyszerre!
  const filteredCompanies = companies.filter(c => {
    const s = searchTerm.toLowerCase();
    const matchesSearch = 
      c.company_name.toLowerCase().includes(s) || 
      (c.brand_name && c.brand_name.toLowerCase().includes(s)) ||
      (c.tax_number && c.tax_number.includes(s)) ||
      (c.industry && c.industry.toLowerCase().includes(s));
      
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    const matchesRole = roleFilter === 'all' || c.role_type === roleFilter;
    return matchesSearch && matchesStatus && matchesRole;
  });

  // Generáljunk egy szép, kétbetűs monogramot a cég nevéből az avatarhoz
  const getInitials = (name) => {
    if (!name) return "??";
    const words = name.split(" ");
    if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-slate-100 flex w-full font-sans antialiased selection:bg-indigo-500 selection:text-white">
      
      {/* 1. SIDEBAR (MODERN SÖTÉT DIZÁJN) */}
      <div className="w-64 bg-slate-950 text-slate-200 p-6 flex flex-col justify-between shrink-0 shadow-xl border-r border-slate-800">
        <div>
          <div className="flex items-center space-x-3 mb-10 px-2">
            <div className="bg-indigo-600 text-white font-black text-xl w-9 h-9 flex items-center justify-center rounded-xl shadow-md shadow-indigo-500/20">O</div>
            <span className="text-lg font-bold tracking-tight text-white">Optitex <span className="text-indigo-400 font-medium">ERP</span></span>
          </div>
          <nav className="space-y-1">
            <button onClick={() => setActiveMenu('dashboard')} className={`w-full flex items-center space-x-3 py-3 px-4 rounded-xl text-sm font-semibold transition ${activeMenu === 'dashboard' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/15' : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'}`}>
              <span>📊</span> <span>Vezérlőpult</span>
            </button>
            <button onClick={() => setActiveMenu('customers')} className={`w-full flex items-center space-x-3 py-3 px-4 rounded-xl text-sm font-semibold transition ${activeMenu === 'customers' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/15' : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'}`}>
              <span>👥</span> <span>Ügyfelek & Partnerek</span>
            </button>
          </nav>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
          <div className="text-left">
            <p className="text-xs font-bold text-slate-300">Balázs Péter</p>
            <p className="text-[10px] text-slate-500 font-medium">Adminisztrátor</p>
          </div>
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
        </div>
      </div>

      {/* 2. FŐ ADATTERÜLET */}
      <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
        
        {/* FELSŐ SÁV */}
        <header className="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-8 shrink-0 shadow-sm z-10">
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">
            {activeMenu === 'dashboard' ? 'Vállalati Áttekintés' : 'CRM & Partner Nyilvántartás'}
          </h2>
          <div className="flex items-center space-x-4">
            <div className="bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
              <span>Supabase Adatbázis: Kapcsolódva</span>
            </div>
          </div>
        </header>

        {/* TARTALOM GÖRGETHETŐSÉGE */}
        <div className="flex-1 p-8 overflow-y-auto">
          
          {/* TARTALOM: VEZÉRLŐPULT */}
          {activeMenu === 'dashboard' && (
            <div className="text-center py-20 text-slate-400">
              <p className="text-4xl mb-4">📈</p>
              <h3 className="text-lg font-bold text-slate-700">A Vezérlőpult pimpelése hamarosan következik...</h3>
              <p className="text-sm mt-1">Kattints az "Ügyfelek & Partnerek" menüpontra a bal oldalon!</p>
            </div>
          )}

          {/* TARTALOM: PIMPELT ÜGYFÉLLISTA */}
          {activeMenu === 'customers' && (
            <div className="space-y-6">
              
              {/* GYORS STATISZTIKA WIDGETEK (FAZON) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Összes partner</p>
                    <p className="text-2xl font-black text-slate-900 mt-0.5">{companies.length}</p>
                  </div>
                  <div className="w-10 h-10 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-center text-lg">📁</div>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Megrendelő (B2B/B2C)</p>
                    <p className="text-2xl font-black text-emerald-600 mt-0.5">{companies.filter(c => c.role_type === 'customer').length}</p>
                  </div>
                  <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center text-lg text-emerald-600">🛍️</div>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Anyag beszállító</p>
                    <p className="text-2xl font-black text-indigo-600 mt-0.5">{companies.filter(c => c.role_type === 'supplier').length}</p>
                  </div>
                  <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center text-lg text-indigo-600">🧵</div>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Alvállalkozó üzem</p>
                    <p className="text-2xl font-black text-purple-600 mt-0.5">{companies.filter(c => c.role_type === 'subcontractor').length}</p>
                  </div>
                  <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center text-lg text-purple-600">🪡</div>
                </div>
              </div>

              {/* SZŰRŐSÁV + KERESŐ (PRÉMIUM TARTALOM) */}
              <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-center">
                <div className="flex flex-wrap gap-3 items-center flex-1 w-full">
                  <div className="relative flex-1 min-w-[260px]">
                    <span className="absolute left-3 top-2.5 text-slate-400 text-sm">🔍</span>
                    <input 
                      type="text" 
                      placeholder="Keresés névre, márkára, adószámra, profilra..." 
                      className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition placeholder:text-slate-400" 
                      value={searchTerm} 
                      onChange={(e) => setSearchTerm(e.target.value)} 
                    />
                  </div>
                  <select className="border border-slate-200 rounded-xl p-2 text-sm bg-slate-50 text-slate-700 font-medium focus:outline-none cursor-pointer" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                    <option value="all">Minden státusz</option>
                    <option value="active">🟢 Csak aktív</option>
                    <option value="inactive">🔴 Csak inaktív</option>
                  </select>
                  <select className="border border-slate-200 rounded-xl p-2 text-sm bg-slate-50 text-slate-700 font-medium focus:outline-none cursor-pointer" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
                    <option value="all">Minden szerepkör</option>
                    <option value="customer">Megrendelők</option>
                    <option value="supplier">Beszállítók</option>
                    <option value="subcontractor">Alvállalkozók</option>
                  </select>
                </div>
                <button onClick={() => setIsModalOpen(true)} className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-5 py-2.5 rounded-xl text-sm shadow-md shadow-indigo-600/10 transition transform active:scale-95 cursor-pointer shrink-0">
                  + Új partner rögzítése
                </button>
              </div>

              {/* PARTNER KÁRTYÁK RÁCSOS ELRENDEZÉSBEN */}
              {loading ? (
                <div className="text-center p-12 text-slate-500 font-medium">Adatok szinkronizálása a felhővel...</div>
              ) : filteredCompanies.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-slate-300 text-slate-400 font-medium">
                  Nincs a keresési feltételeknek megfelelő ügyfél az adatbázisban.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {filteredCompanies.map((company) => {
                    const mainContact = company.contacts && company.contacts.length > 0 ? company.contacts[0] : null;
                    
                    return (
                      <div key={company.id} className={`bg-white rounded-2xl border transition-all duration-200 flex flex-col justify-between hover:shadow-xl hover:border-slate-300 relative overflow-hidden group ${company.status === 'inactive' ? 'border-slate-200 bg-slate-50/50 opacity-75' : 'border-slate-200/70 shadow-sm'}`}>
                        
                        {/* FELSŐ SZEKCIÓ VIZUÁLIS ELEMEKKEL */}
                        <div className="p-6 text-left">
                          <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center space-x-3">
                              {/* AVATAR (FAZON) */}
                              <div className={`w-11 h-11 rounded-xl font-bold text-sm flex items-center justify-center border ${company.role_type === 'customer' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : company.role_type === 'supplier' ? 'bg-indigo-50 text-indigo-700 border-indigo-100' : 'bg-purple-50 text-purple-700 border-purple-100'}`}>
                                {getInitials(company.company_name)}
                              </div>
                              <div>
                                <h3 className="font-extrabold text-slate-900 text-base leading-tight group-hover:text-indigo-600 transition-colors m-0">{company.company_name}</h3>
                                {company.brand_name ? (
                                  <span className="text-xs font-semibold text-indigo-500 bg-indigo-50 px-1.5 py-0.5 rounded mt-1 inline-block">✨ Brand: {company.brand_name}</span>
                                ) : (
                                  <span className="text-xs text-slate-400 font-medium mt-0.5 inline-block">Nincs külön márkanév</span>
                                )}
                              </div>
                            </div>
                            
                            {/* STÁTUSZ JELZŐ CÍMKE */}
                            <span className={`text-[10px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded-full ${company.status === 'active' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'}`}>
                              {company.status === 'active' ? 'Aktív' : 'Inaktív'}
                            </span>
                          </div>

                          {/* IPARÁG / SZEREPKÖR JELZŐK */}
                          <div className="flex gap-1.5 mb-4">
                            <span className="text-[10px] font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">🏢 {company.industry}</span>
                            <span className="text-[10px] font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                              {company.company_type === 'business' ? '💼 Céges partner' : '👤 Magánszemély'}
                            </span>
                          </div>

                          {/* ADAT MATRIX (IKONOKKAL FINOMÍTVA) */}
                          <div className="text-xs space-y-2 text-slate-600 bg-slate-50/80 p-3.5 rounded-xl border border-slate-200/40 mb-4 font-medium">
                            <p className="flex items-center space-x-2 truncate"><span className="text-slate-400 text-sm">📄</span> <span><strong className="text-slate-700">Adószám:</strong> {company.tax_number || '---'}</span></p>
                            {company.eu_tax_number && <p className="flex items-center space-x-2"><span className="text-slate-400 text-sm">🌍</span> <span><strong className="text-slate-700">EU Tax:</strong> {company.eu_tax_number}</span></p>}
                            <p className="flex items-center space-x-2"><span className="text-slate-400 text-sm">💰</span> <span><strong className="text-slate-700">Pénzügy:</strong> {company.payment_terms} nap | {company.currency}</span></p>
                            {company.billing_address && <p className="flex items-center space-x-2 truncate" title={company.billing_address}><span className="text-slate-400 text-sm">📍</span> <span><strong className="text-slate-700">Cím:</strong> {company.billing_address}</span></p>}
                          </div>

                          {/* FŐ KAPCSOLATTARTÓ BOX (PRÉMIUM TARTALOM + GYORS AKCIÓK) */}
                          <div className="border border-slate-100 rounded-xl p-3 bg-white shadow-inner relative">
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Elsődleges Kontakt ({company.contacts?.length || 0})</p>
                            {mainContact ? (
                              <div className="flex justify-between items-center">
                                <div>
                                  <p className="text-xs font-bold text-slate-800">{mainContact.name}</p>
                                  <p className="text-[11px] text-slate-500 font-medium">{mainContact.role}</p>
                                </div>
                                {/* Gyors akciók ikonjai */}
                                <div className="flex space-x-1">
                                  {mainContact.phone && <a href={`tel:${mainContact.phone}`} className="w-6 h-6 bg-slate-50 hover:bg-indigo-50 border border-slate-200 rounded-md flex items-center justify-center text-xs transition" title="Hívás indítása">📞</a>}
                                  {mainContact.email && <a href={`mailto:${mainContact.email}`} className="w-6 h-6 bg-slate-50 hover:bg-indigo-50 border border-slate-200 rounded-md flex items-center justify-center text-xs transition" title="Email küldése">✉</a>}
                                </div>
                              </div>
                            ) : (
                              <p className="text-xs italic text-slate-400 m-0">Nincs megadva kapcsolattartó.</p>
                            )}
                          </div>

                          {/* POST-IT JELLEGŰ BELSŐ JEGYZET (TARTALOM TUNING) */}
                          {company.internal_notes && (
                            <div className="mt-3 bg-amber-50 border border-amber-200/70 p-2.5 rounded-xl text-[11px] text-amber-800 font-medium flex items-start space-x-1.5 shadow-sm">
                              <span className="text-xs mt-0.5">⚠️</span>
                              <p className="m-0 leading-tight"><strong>Belső megjegyzés:</strong> {company.internal_notes}</p>
                            </div>
                          )}

                        </div>

                        {/* ALSÓ AKCIÓSÁV (FAZON TISZTÍTÁS) */}
                        <div className="bg-slate-50 border-t border-slate-100 px-6 py-3 flex justify-between items-center rounded-b-2xl">
                          <button onClick={() => openEditModal(company)} className="text-xs text-indigo-600 hover:text-indigo-800 font-bold px-3 py-1.5 rounded-lg hover:bg-indigo-50 border border-transparent hover:border-indigo-100 transition cursor-pointer">
                            Adatlap / Módosítás
                          </button>
                          <button onClick={() => handleDelete(company.id)} className="text-xs text-slate-400 hover:text-red-600 font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Törlés
                          </button>
                        </div>

                      </div>
                    );
                  })}
                </div>
              )}

            </div>
          )}

        </div>
      </div>

      {/* ================= FELUGRÓ MODAL ABLAK (FAZONRA ÉS STRUKTÚRÁRA IS SZÉPÍTVE) ================= */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-md flex items-center justify-center z-50 p-4 transition-all duration-300">
          <div className="bg-white rounded-3xl w-full max-w-xl shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto flex flex-col text-left transform scale-100 animate-in zoom-in-95 duration-150">
            
            {/* MODAL FEJLÉC */}
            <div className="p-6 border-b border-slate-100 flex justify-between items-center shrink-0">
              <h3 className="text-lg font-black text-slate-900 tracking-tight">
                {editingCompanyId ? '🔒 Partner adatlap finomhangolása' : '🚀 Új komplex partner regisztráció'}
              </h3>
              <button onClick={closeModal} className="w-8 h-8 bg-slate-50 hover:bg-slate-100 text-slate-400 hover:text-slate-700 border border-slate-200 rounded-full font-bold flex items-center justify-center text-xs transition cursor-pointer">✕</button>
            </div>

            {/* FÜL NAVIGÁCIÓ (PIMPELT DESIGN) */}
            <div className="bg-slate-50 px-6 pt-3 border-b border-slate-100 flex space-x-6 shrink-0">
              <button type="button" onClick={() => setActiveFormTab('basic')} className={`pb-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer ${activeFormTab === 'basic' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'}`}>1. Alapadatok</button>
              <button type="button" onClick={() => setActiveFormTab('finance')} className={`pb-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer ${activeFormTab === 'finance' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'}`}>2. Pénzügy & Címek</button>
              <button type="button" onClick={() => setActiveFormTab('contacts')} className={`pb-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer ${activeFormTab === 'contacts' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'}`}>3. Kontaktok & Jegyzet</button>
            </div>

            {/* MODAL TÖRZS / ŰRLAP */}
            <form onSubmit={handleSubmit} className="flex-1 p-6 overflow-y-auto space-y-4">
              
              {/* TAB 1: ALAPOK */}
              {activeFormTab === 'basic' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl border border-slate-200/50">
                    <button type="button" onClick={() => setCompanyForm({...companyForm, company_type: 'business'})} className={`py-1.5 text-xs font-bold rounded-lg transition cursor-pointer ${companyForm.company_type === 'business' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500'}`}>Cég (B2B)</button>
                    <button type="button" onClick={() => setCompanyForm({...companyForm, company_type: 'individual'})} className={`py-1.5 text-xs font-bold rounded-lg transition cursor-pointer ${companyForm.company_type === 'individual' ? 'bg-white text-pink-600 shadow-sm' : 'text-slate-500'}`}>Magánszemély / Márka</button>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Hivatalos Cégnév / Nyilvántartott Név *</label>
                    <input type="text" required className="w-full border border-slate-200 rounded-xl p-2.5 text-sm focus:outline-none focus:border-indigo-500 transition" value={companyForm.company_name} onChange={(e) => setCompanyForm({...companyForm, company_name: e.target.value})} placeholder="Pl. Optitex Textilipari Kft." />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Kereskedelmi Márkanév (Brand)</label>
                    <input type="text" className="w-full border border-slate-200 rounded-xl p-2.5 text-sm focus:outline-none focus:border-indigo-500 transition" value={companyForm.brand_name} onChange={(e) => setCompanyForm({...companyForm, brand_name: e.target.value})} placeholder="Pl. OptiWear" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">ERP Szerepkör</label>
                      <select className="w-full border border-slate-200 rounded-xl p-2.5 text-sm bg-white focus:outline-none" value={companyForm.role_type} onChange={(e) => setCompanyForm({...companyForm, role_type: e.target.value})}>
                        <option value="customer">Megrendelő (Márka / Bérgyártás)</option>
                        <option value="supplier">Beszállító (Méteráru / Kellékek)</option>
                        <option value="subcontractor">Alvállalkozó (Szabászat / Nyomás)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Iparág / Fő profil</label>
                      <input type="text" className="w-full border border-slate-200 rounded-xl p-2.5 text-sm focus:outline-none" value={companyForm.industry} onChange={(e) => setCompanyForm({...companyForm, industry: e.target.value})} />
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: PÉNZÜGY & CÍMEK */}
              {activeFormTab === 'finance' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Hazai Adószám</label>
                      <input type="text" className="w-full border border-slate-200 rounded-xl p-2.5 text-sm" value={companyForm.tax_number} onChange={(e) => setCompanyForm({...companyForm, tax_number: e.target.value})} placeholder="12345678-2-42" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Közösségi (EU) Adószám</label>
                      <input type="text" className="w-full border border-slate-200 rounded-xl p-2.5 text-sm" value={companyForm.eu_tax_number} onChange={(e) => setCompanyForm({...companyForm, eu_tax_number: e.target.value})} placeholder="HU12345678" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Fizetési feltétel (nap)</label>
                      <select className="w-full border border-slate-200 rounded-xl p-2.5 text-sm bg-white" value={companyForm.payment_terms} onChange={(e) => setCompanyForm({...companyForm, payment_terms: e.target.value})}>
                        <option value="0">Azonnali / Készpénz / Előreutalás</option>
                        <option value="8">8 napos banki átutalás</option>
                        <option value="15">15 napos banki átutalás</option>
                        <option value="30">30 napos banki átutalás</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Alapértelmezett Valuta</label>
                      <select className="w-full border border-slate-200 rounded-xl p-2.5 text-sm bg-white" value={companyForm.currency} onChange={(e) => setCompanyForm({...companyForm, currency: e.target.value})}>
                        <option value="HUF">HUF (Ft)</option>
                        <option value="EUR">EUR (€)</option>
                        <option value="USD">USD ($)</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Számlázási Cím</label>
                    <input type="text" className="w-full border border-slate-200 rounded-xl p-2.5 text-sm" value={companyForm.billing_address} onChange={(e) => setCompanyForm({...companyForm, billing_address: e.target.value})} placeholder="Város, utca, házszám, irányítószám" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Szállítási Telephely Címe</label>
                    <input type="text" className="w-full border border-slate-200 rounded-xl p-2.5 text-sm" value={companyForm.shipping_address} onChange={(e) => setCompanyForm({...companyForm, shipping_address: e.target.value})} placeholder="Gyár, raktár vagy átvételi pont címe" />
                  </div>
                </div>
              )}

              {/* TAB 3: CONTACTS & NOTES */}
              {activeFormTab === 'contacts' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">⚠️ Belső figyelmeztetés / Textilipari kritikus megjegyzés</label>
                    <textarea rows="2" className="w-full border border-slate-200 rounded-xl p-2.5 text-sm bg-amber-50/20 focus:bg-white transition" value={companyForm.internal_notes} onChange={(e) => setCompanyForm({...companyForm, internal_notes: e.target.value})} placeholder="Pl. Szabás előtt avatni kell az anyagot! Mintadarab jóváhagyása kötelező!" />
                  </div>

                  <div className="border-t border-slate-100 pt-3">
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="text-xs font-black text-slate-800 uppercase tracking-wider">Kapcsolattartók Kezelése</h4>
                      <button type="button" onClick={addContactField} className="text-xs text-indigo-600 bg-indigo-50 border border-indigo-100 hover:bg-indigo-100 px-3 py-1 rounded-xl font-bold transition cursor-pointer">+ Új kontakt</button>
                    </div>
                    
                    <div className="space-y-3 max-h-[160px] overflow-y-auto pr-1">
                      {companyForm.contacts.map((contact, index) => (
                        <div key={index} className="bg-slate-50 p-3 rounded-xl border border-slate-200 relative grid grid-cols-2 gap-2 text-xs shadow-inner">
                          <button type="button" onClick={() => removeContactField(index)} className="absolute -top-1 -right-1 bg-red-100 text-red-600 rounded-full w-5 h-5 flex items-center justify-center font-bold shadow-sm cursor-pointer hover:bg-red-200">✕</button>
                          <input type="text" placeholder="Név *" required className="border border-slate-200 p-2 rounded-lg bg-white" value={contact.name} onChange={(e) => handleContactChange(index, 'name', e.target.value)} />
                          <input type="text" placeholder="Beosztás (pl. Pénzügy)" className="border border-slate-200 p-2 rounded-lg bg-white" value={contact.role} onChange={(e) => handleContactChange(index, 'role', e.target.value)} />
                          <input type="email" placeholder="Email cím" className="border border-slate-200 p-2 rounded-lg bg-white" value={contact.email} onChange={(e) => handleContactChange(index, 'email', e.target.value)} />
                          <input type="text" placeholder="Telefonszám" className="border border-slate-200 p-2 rounded-lg bg-white" value={contact.phone} onChange={(e) => handleContactChange(index, 'phone', e.target.value)} />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ALULSÓ VEZÉRLÉS */}
              <div className="flex justify-between space-x-3 pt-4 border-t border-slate-100 shrink-0">
                <div className="flex space-x-2">
                  {activeFormTab !== 'basic' && <button type="button" onClick={() => setActiveFormTab(activeFormTab === 'contacts' ? 'finance' : 'basic')} className="px-3 py-2 text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition">← Vissza</button>}
                  {activeFormTab !== 'contacts' && <button type="button" onClick={() => setActiveFormTab(activeFormTab === 'basic' ? 'finance' : 'contacts')} className="px-3 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-600/10 transition">Következő →</button>}
                </div>
                <div className="flex space-x-2">
                  <button type="button" onClick={closeModal} className="px-4 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-100 rounded-xl">Mégse</button>
                  <button type="submit" className="px-5 py-2 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md shadow-emerald-600/10 transition cursor-pointer">Adatok rögzítése</button>
                </div>
              </div>

            </form>
          </div>
        </div>
      )}

    </div>
  );
}