import {useQuery} from '@tanstack/react-query';
import {BarElement,CategoryScale,Chart as ChartJS,Legend,LinearScale,Tooltip} from 'chart.js';
import {Bar} from 'react-chartjs-2';
import {Briefcase,Globe2,Sparkles,Users} from 'lucide-react';
import {useNavigate} from 'react-router-dom';
import {api} from '../api/client';
import type {Analytics} from '../types';

ChartJS.register(CategoryScale,LinearScale,BarElement,Tooltip,Legend);
const integerFormatter=new Intl.NumberFormat('fa-IR');
const decimalFormatter=new Intl.NumberFormat('fa-IR',{minimumFractionDigits:1,maximumFractionDigits:1});

export function DashboardPage(){const nav=useNavigate();const q=useQuery({queryKey:['analytics'],queryFn:({signal})=>api.get<Analytics>('/analytics/overview',signal)});if(q.isLoading)return <div className="page state">در حال دریافت گزارش‌ها…</div>;if(!q.data)return <div className="page state">گزارش‌ها در دسترس نیستند.</div>;const {kpis,charts}=q.data;return <div className="page dashboard"><div className="eyebrow">تحلیل نیروی انسانی</div><h1>نمای کلی استعدادها</h1><p className="lead">نمایی به‌روز از شبکهٔ پروفایل‌های ایندکس‌شده.</p><section className="kpis"><Kpi icon={<Users/>} label="پروفایل‌ها" value={integerFormatter.format(kpis.total)}/><Kpi icon={<Sparkles/>} label="مهارت‌های یکتا" value={integerFormatter.format(kpis.unique_skills)}/><Kpi icon={<Globe2/>} label="کشورها" value={integerFormatter.format(kpis.countries)}/><Kpi icon={<Briefcase/>} label="میانگین سابقه" value={`${decimalFormatter.format(Number(kpis.average_experience||0))} سال`}/></section><section className="chart-grid"><Chart title="مهارت‌های برتر" data={charts.top_skills||[]} color="#10a37f" onClick={label=>nav(`/search?skills=${encodeURIComponent(label)}`)}/><Chart title="صنایع" data={charts.top_industries||[]} color="#7857d8" onClick={label=>nav(`/search?industry=${encodeURIComponent(label)}`)}/><Chart title="نقش‌های شغلی فعلی" data={charts.top_job_roles||[]} color="#d97706" onClick={label=>nav(`/search?job_title=${encodeURIComponent(label)}`)}/><Chart title="توزیع سابقهٔ کاری" data={charts.experience_distribution||[]} color="#2675d8" onClick={()=>{}}/></section></div>}
function Kpi({icon,label,value}:{icon:React.ReactNode;label:string;value:string|number}){return <article>{icon}<div><strong>{value}</strong><span>{label}</span></div></article>}
function Chart({title,data,color,onClick}:{title:string;data:{label:string;count:number}[];color:string;onClick:(x:string)=>void}){return <article className="chart"><h2>{title}</h2><p>برای مشاهدهٔ پروفایل‌های مرتبط، روی هر میله کلیک کنید.</p>{data.length?<Bar options={{responsive:true,indexAxis:'y',locale:'fa-IR',plugins:{legend:{display:false}},onClick:(_,els)=>{if(els[0])onClick(data[els[0].index].label)}}} data={{labels:data.map(x=>x.label),datasets:[{data:data.map(x=>x.count),backgroundColor:color,borderRadius:5}]}}/>:<div className="chart-empty">برای نمایش نمودار، ابتدا داده‌ها را وارد کنید.</div>}</article>}
