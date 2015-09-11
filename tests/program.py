import sys
from operator import contains, not_

from mock import patch, Mock
from spec import eq_, ok_, skip, trap

from invoke import Program, Collection

from _utils import load, cd, IntegrationSpec, expect


class Program_(IntegrationSpec):
    class init:
        "__init__"
        def may_specify_version(self):
            eq_(Program(version='1.2.3').version, '1.2.3')

        def default_version_is_unknown(self):
            eq_(Program().version, 'unknown')

        def may_specify_namespace(self):
            foo = load('foo')
            ok_(Program(namespace=foo).namespace is foo)

        def may_specify_name(self):
            eq_(Program(name='Myapp').name, 'Myapp')

        def may_specify_binary(self):
            eq_(Program(binary='myapp').binary, 'myapp')

    class normalize_argv:
        @patch('invoke.program.sys')
        def defaults_to_sys_argv(self, mock_sys):
            argv = ['inv', '--version']
            mock_sys.argv = argv
            p = Program()
            p.print_version = Mock()
            p.run()
            p.print_version.assert_called()

        def uses_a_list_unaltered(self):
            p = Program()
            p.print_version = Mock()
            p.run(['inv', '--version'], exit=False)
            p.print_version.assert_called()

        def splits_a_string(self):
            eq_(Program().normalize_argv("foo bar"), ['foo', 'bar'])

    class normalize_name:
        def defaults_to_capitalized_argv_when_None(self):
            expect("myapp --version", out="Myapp unknown\n", invoke=False)

        def uses_overridden_value_when_given(self):
            p = Program(name='NotInvoke')
            expect("--version", out="NotInvoke unknown\n", program=p)

    class normalize_binary:
        def defaults_to_argv_when_None(self):
            expect(
                "myapp --help",
                out="myapp [--core-opts]",
                invoke=False,
                test=contains
            )

        def uses_overridden_value_when_given(self):
            expect(
                "myapp --help",
                out="nope [--core-opts]",
                program=Program(binary='nope'),
                invoke=False,
                test=contains
            )

        @trap
        def use_binary_basename_when_invoked_absolutely(self):
            Program().run("/usr/local/bin/myapp --help", exit=False)
            stdout = sys.stdout.getvalue()
            ok_("myapp [--core-opts]" in stdout)
            ok_("/usr/local/bin" not in stdout)

    class initial_context:
        def contains_truly_core_arguments_regardless_of_namespace_value(self):
            # Spot check. See integration-style --help tests for full argument
            # checkup.
            for program in (Program(), Program(namespace=Collection())):
                for arg in ('--complete', '--debug', '--warn-only'):
                    expect("--help", program=program, out=arg, test=contains)

        def null_namespace_triggers_task_related_args(self):
            program = Program(namespace=None)
            for arg in Program.task_args:
                expect("--help", program=program, out=arg.name, test=contains)

        def non_null_namespace_does_not_trigger_task_related_args(self):
            program = Program(namespace=Collection())
            # NOTE: have to reverse args because of how contains() works
            not_in = lambda a,b: not_(contains(b, a))
            for arg in Program.task_args:
                expect("--help", out=arg.name, test=not_in)

    class run:
        class bundled_namespace:
            class when_None:
                def seeks_and_loads_tasks_module(self):
                    with cd('implicit'):
                        expect('foo', out="Hm\n")

            class when_Collection:
                def does_not_seek(self):
                    with cd('implicit'):
                        expect(
                            'foo',
                            err="No idea what 'foo' is!\n",
                            program=Program(namespace=Collection('blank'))
                        )