To use this module, call the find_reviewer_level function on the
hr.department object, and provide the level attribute as an argument.

This function retrieves reviewers from the specified department and
returns a user.

For example, Department AA has 3 Approvers:

- User A
- User B
- User C

and you need to find the reviewer at level 1, you can use the following
code:

``` python
rec.employee_id.department_id.find_reviewer_level(level=1)
```

The result will be User A.
