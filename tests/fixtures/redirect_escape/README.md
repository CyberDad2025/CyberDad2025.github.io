Hostile redirect_to values for the redirect.html escaping check (blog-generator-off-1127).
Not built with the site (tests/ is excluded). To run: in a scratch worktree copy these 12 .md files
into _posts/, build Jekyll to a scratch destination, then
python3 tests/check_blog_generator_off.py --escape-fixture <that destination>
