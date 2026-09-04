import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {afterEach,describe,expect,it,vi} from 'vitest';

import {SearchPage} from './SearchPage';

const response=(page:number)=>({
  meta:{total:40,page,page_size:20,sort:'relevance',took_ms:1},
  results:[{id:page,full_name:`Profile ${page}`,current_job_title:'Engineer',current_company_name:'Acme',location:{country:'Canada'},inferred_years_experience:5,skills:['Python'],match_reasons:[],highlights:[]}],
  facets:{},
});

function renderPage(){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/search']}><SearchPage/></MemoryRouter></QueryClientProvider>);
}

describe('SearchPage pagination',()=>{
  afterEach(()=>vi.restoreAllMocks());

  it('requests page 2 and can return to page 1',async()=>{
    const fetchMock=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
      const url=String(input);
      const page=new URL(url,'http://localhost').searchParams.get('page');
      return new Response(JSON.stringify(response(page==='2'?2:1)),{status:200,headers:{'Content-Type':'application/json'}});
    });
    renderPage();

    expect(await screen.findByText('Profile 1')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'بعدی'}));
    expect(await screen.findByText('Profile 2')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('page=2'),expect.anything());

    fireEvent.click(screen.getByRole('button',{name:'قبلی'}));
    await waitFor(()=>expect(screen.getByText('Profile 1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button',{name:'بعدی'}));
    expect(await screen.findByText('Profile 2')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('کشور'),{target:{value:'Canada'}});
    expect(await screen.findByText('Profile 1')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/country=Canada(?!.*page=)/),expect.anything());
  });

  it('loads existing skill suggestions after two characters',async()=>{
    const fetchMock=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
      const url=String(input);
      const body=url.includes('/suggestions?')?{suggestions:['Python']}:response(1);
      return new Response(JSON.stringify(body),{status:200,headers:{'Content-Type':'application/json'}});
    });
    renderPage();

    fireEvent.change(await screen.findByLabelText('جست‌وجوی پروفایل‌ها'),{target:{value:'py'}});
    await waitFor(()=>expect(document.querySelector('option[value="Python"]')).not.toBeNull());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('suggestions?type=skill&q=py'),expect.anything());
  });
});
