export type Facet={value:string;count:number};
export type SearchResult={id:number;full_name:string;current_job_title:string;current_company_name:string;location:{country?:string;region?:string;locality?:string};inferred_years_experience:number|null;skills:string[];match_reasons:{type:string;label:string}[];highlights:{field:string;text:string}[]};
export type SearchResponse={meta:{total:number;page:number;page_size:number;sort:string;took_ms:number};results:SearchResult[];facets:Record<string,Facet[]>};
export type SuggestionsResponse={suggestions:string[]};
export type Profile=SearchResult&{summary:string;primary_email:string;mobile_phone:string;linkedin_url?:string;experiences:Array<{id:number;title:string;company_name:string;start_date?:string;end_date?:string;summary:string;is_primary:boolean}>;educations:Array<{id:number;school_name:string;degrees:string[];majors:string[];start_date?:string;end_date?:string}>};
export type Analytics={kpis:{total:number;countries:number;average_experience:number|null;unique_skills:number};charts:Record<string,{label:string;count:number}[]>};
