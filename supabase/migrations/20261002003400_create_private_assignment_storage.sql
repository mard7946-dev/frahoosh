insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('assignment-files','assignment-files',false,10485760,array['image/jpeg','image/png','image/webp','application/pdf'])
on conflict(id) do update set file_size_limit=10485760,allowed_mime_types=excluded.allowed_mime_types;
drop policy if exists assignment_files_insert on storage.objects;
create policy assignment_files_insert on storage.objects for insert to authenticated
with check(bucket_id='assignment-files' and (storage.foldername(name))[1]=(select auth.uid()::text));
drop policy if exists assignment_files_select on storage.objects;
create policy assignment_files_select on storage.objects for select to authenticated
using(bucket_id='assignment-files' and ((storage.foldername(name))[1]=(select auth.uid()::text) or private.frahoosh_is_staff()));
drop policy if exists assignment_files_delete on storage.objects;
create policy assignment_files_delete on storage.objects for delete to authenticated
using(bucket_id='assignment-files' and ((storage.foldername(name))[1]=(select auth.uid()::text) or private.frahoosh_is_staff()));