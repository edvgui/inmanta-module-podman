# Description

* Short description here *

closes *Add ticket reference here*

note: to add a changelog entry and bump the version number:
`inmanta module release --dev [--major|--minor|--patch] [--changelog-message "<your_changelog_message>"]`

# [Merge procedure](https://internal.inmanta.com/development/core/tasks/commiting-changes-modules.html)

1. merge using the merge button
2. tag and bump

```sh
git checkout master
git pull
inmanta module release
git push
git push {tag} # push the tag as well
```
3. Remove the branch

# Self Check:

Strike through any lines that are not applicable (`~~line~~`) then check the box

- [ ] Attached issue to pull request
- [ ] Changelog entry
- [ ] Version number is bumped to dev version
- [ ] Code is clear and sufficiently documented
- [ ] Sufficient test cases (reproduces the bug/tests the requested feature)
- [ ] Correct, in line with design
- [ ] End user documentation is included or an issue is created for end-user documentation (add ref to issue here: )
